"""Validate one mobile QA run and print its per-platform evidence row.

    python3 -B .ai/scripts/qa_evidence.py <run directory> --expected-artifact <identity>
        [--expected-sha256 <hex>] [--catalog <scenario catalog>]

The run directory is either a maestro-cli output directory (it holds `maestro-cli-result.json` and `report.xml`) or
an appium-real-device-testing release artifact root (it holds `run-summary.json` and `lease-release.json`). The
tool reads only the fields those launchers write; it never runs a device, a lease command or the network.

One run gives one row: platform, device key and name, lease ID, installed app identity, artifact SHA-256, flow
results, lease released and cleanup proven. The row passes only when every field is present, the installed
identity equals `--expected-artifact` (and the artifact digest equals `--expected-sha256` when given), every flow
passed, the exact lease was released and cleanup was proven. Anything missing, malformed or mismatched fails the
row with a named reason.

Identity format: `<platform>:<app id>@<build>#<40-hex source commit>` for maestro-cli runs, where the build is the
pubspec build number (iOS) or the installed versionCode (Android), and `<platform>:<app id>@<version-build>` for
appium runs, which record no source commit.

Artifact digest: maestro-cli rows take it from the launcher's install readback (iOS: the installed bundle manifest
equals the built one; Android: the installed APK hash equals the reviewed APK). Appium rows take
`installed_artifact_sha256` and `installed_artifact_source` from run-summary.json, and bind them to
`installed_artifact_readback`: on Android (`installed-split-apks`) the digest is recomputed from the readback
split files, SHA-256 over the sorted `<split-name> <sha256>` lines; on iOS (`uploaded-ipa`, present only
when the run was given `--ios-ipa-path`) it is the uploaded IPA's digest, bound to the device's bundle ID, version and
build readback, which proves which upload was installed, not the on-device bytes. The row records the source
(`artifact_source`, null for maestro-cli rows).

The row holds no device UDID or serial and no absolute path: the device appears as the launcher's device key
(SHA-256 of `<platform>:<device id>`, iOS UDIDs in upper case) and a device name: for maestro-cli the simulator or
AVD display name, for appium the lab's logical device ID (such as `iphone-13-mini`). Prints one JSON object; exit 0
when the row passed, 1 when it failed, 2 when the directory is not a readable run.

With `--catalog` (the project's scenario catalog, see scenarios.py), each maestro-cli flow result also lists the
`scenarios` of the row's platform whose `maestroFlow` is that flow, so the row and the QA verdict name the same scenario IDs. Appium flows
are runner steps and list none. An invalid catalog is unreadable input (exit 2)."""
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from qa_contract import ContractError,read_json_file
from scenarios import catalog_errors

MAESTRO_RESULT='maestro-cli-result.json'
MAESTRO_REPORT='report.xml'
APPIUM_SUMMARY='run-summary.json'
APPIUM_RELEASE='lease-release.json'
# Registered runtime states the lease release itself counts as gone (physical_device_lease.py). A reused PID
# whose original process is absent is not a live owned process; identity drift on the same birth still is.
RUNTIME_ABSENT=frozenset({'absent','pid_reused_original_absent'})
SNAPSHOT_DIR='trusted-repo-snapshot'
PLATFORMS=('ios','android')
SHA256=re.compile('[0-9a-f]{64}')
COMMIT=re.compile('[0-9a-f]{40}')
BUILD=re.compile('[1-9][0-9]*')
APP_ID=re.compile(r'[A-Za-z0-9_][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_][A-Za-z0-9_-]*)+')
APPIUM_FLOW_PREFIX='appium_command_'
APPIUM_ARTIFACT_SOURCES={'android':'installed-split-apks','ios':'uploaded-ipa'}

class Unreadable(RuntimeError):pass

def device_key(platform,device_id):
    """The maestro-cli device key: SHA-256 of `<platform>:<device id>` with an iOS UDID in upper case."""
    normalized=device_id.upper() if platform=='ios' else device_id
    return hashlib.sha256(f'{platform}:{normalized}'.encode()).hexdigest()

def read_json(path):
    try:data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,UnicodeDecodeError,json.JSONDecodeError) as error:raise Unreadable(f'{path.name}:{type(error).__name__}')
    if not isinstance(data,dict):raise Unreadable(f'{path.name}:not_an_object')
    return data

def obj(value):return value if isinstance(value,dict) else {}
def text(value):return value if isinstance(value,str) and value else None

class Row:
    def __init__(self,source):
        self.source=source;self.failures=[]
        self.fields={'source':source,'platform':None,'device_key':None,'device_name':None,'lease_id':None,
                     'identity':None,'app_id':None,'build':None,'source_commit':None,'artifact_sha256':None,'artifact_source':None,
                     'flows':[],'lease_released':False,'cleanup_proven':False}
    def fail(self,code):
        if code not in self.failures:self.failures.append(code)
    def need(self,value,code):
        if not value:self.fail(code)
        return bool(value)
    def result(self):
        return {**self.fields,'result':'FAIL' if self.failures else 'PASS','failures':self.failures}

def check_identity(row,expected_artifact,expected_sha256):
    platform,app_id,build=row.fields['platform'],row.fields['app_id'],row.fields['build']
    commit,artifact=row.fields['source_commit'],row.fields['artifact_sha256']
    if not row.need(platform in PLATFORMS,'platform_invalid'):return
    complete=row.need(isinstance(app_id,str) and APP_ID.fullmatch(app_id),'app_id_missing')
    complete=row.need(isinstance(build,str) and build,'build_missing') and complete
    if row.need(artifact is not None,'artifact_sha256_missing'):
        row.need(isinstance(artifact,str) and SHA256.fullmatch(artifact),'artifact_sha256_invalid')
    if row.source=='maestro-cli':
        complete=row.need(isinstance(commit,str) and COMMIT.fullmatch(commit),'source_commit_missing') and complete
        identity=f'{platform}:{app_id}@{build}#{commit}'
    else:identity=f'{platform}:{app_id}@{build}'
    if not complete:return  # no identity to compare; the missing parts already fail the row
    row.fields['identity']=identity
    if expected_artifact!=identity:row.fail('identity_mismatch')
    if expected_sha256 is not None and expected_sha256!=artifact:row.fail('artifact_sha256_mismatch')

def same(row,before,after,code):
    """Pre-run and post-run provenance: both present and equal."""
    row.need(isinstance(before,dict) and before and before==after,code)

def junit_flows(row,run,result,repo_root):
    """Per-flow results from report.xml, matched to the result's flow list through the trusted snapshot paths."""
    flows=result.get('flows')
    if not row.need(isinstance(flows,list) and flows and all(isinstance(f,str) for f in flows),'flows_missing'):return
    names=[]
    for flow in flows:
        path=Path(flow)
        try:names.append(path.relative_to(repo_root).as_posix() if repo_root else None)
        except ValueError:names.append(None)
    if not row.need(all(names),'flow_outside_repo'):return
    try:root=ET.parse(run/MAESTRO_REPORT).getroot()
    except (OSError,ET.ParseError):
        row.fail('junit_report_missing');row.fields['flows']=[{'flow':n,'result':'NOT_RUN'} for n in names];return
    found={}
    for case in root.iter('testcase'):
        file=case.get('file') or ''
        marker=f'/{SNAPSHOT_DIR}/'
        relative=file.split(marker,1)[1] if marker in file else None
        status=case.get('status')
        failed=case.find('failure') is not None or case.find('error') is not None
        if relative is None or relative in found:row.fail('junit_report_malformed');continue
        found[relative]='PASS' if status=='SUCCESS' and not failed else 'FAIL'
    if set(found)!=set(names):row.fail('junit_flows_mismatch')
    row.fields['flows']=[{'flow':n,'result':found.get(n,'NOT_RUN')} for n in names]

def maestro_row(run,expected_artifact,expected_sha256):
    result=read_json(run/MAESTRO_RESULT)
    row=Row('maestro-cli');f=row.fields
    row.need(result.get('schema_version')==2,'schema_version_unsupported')
    row.need(result.get('transport')=='maestro_cli','transport_not_maestro_cli')
    platform=result.get('platform');f['platform']=platform
    device_id=text(result.get('device_id'));session=text(result.get('session_id'))
    lease,release,exclusion=obj(result.get('lease')),obj(result.get('release')),obj(result.get('physical_exclusion'))
    if row.need(device_id,'device_missing') and platform in PLATFORMS:f['device_key']=device_key(platform,device_id)
    f['device_name']=text(lease.get('name'));f['lease_id']=session
    row.need(session,'lease_id_missing')
    row.need(f['device_name'],'device_name_missing')
    row.need(lease.get('device_id')==device_id and lease.get('platform')==platform,'lease_device_mismatch')
    # Schema v2 provenance: one immutable launcher, pinned Python and lease authority, equal before and after.
    launcher=obj(result.get('launcher'))
    row.need(isinstance(launcher.get('launcher_deployment_id'),str) and COMMIT.fullmatch(launcher['launcher_deployment_id'])
             and isinstance(launcher.get('launcher_sha256'),str) and SHA256.fullmatch(launcher['launcher_sha256']),
             'launcher_provenance_missing')
    same(row,result.get('launcher'),result.get('launcher_post_run'),'launcher_changed')
    same(row,result.get('python_runtime'),result.get('python_runtime_post_run'),'python_runtime_changed')
    same(row,result.get('lease_authority'),result.get('lease_authority_post_run'),'lease_authority_changed')
    # Release: the requested device and this session, nothing retained, the device marker released.
    released=(result.get('release_verified') is True and release.get('released_device_id')==device_id
              and release.get('session_id')==session and release.get('lease_retained',False) is False)
    exclusion_released=(exclusion.get('state')=='released' and exclusion.get('scope')=='device'
                        and exclusion.get('device_id')==device_id and exclusion.get('session_id')==session)
    row.need(released,'lease_not_released');row.need(exclusion_released,'device_exclusion_not_released')
    f['lease_released']=released and exclusion_released
    cleanup=result.get('cleanup_completed') is True
    reconciliation=result.get('derived_transaction_reconciliation')
    if reconciliation is not None:
        reconciliation=obj(reconciliation)
        cleanup=cleanup and reconciliation.get('remaining_transaction_count')==0 and reconciliation.get('remaining_publication_count')==0
    source_head=text(result.get('source_head'))
    if platform=='ios':
        install=result.get('app_install');f['source_commit']=source_head
        if row.need(isinstance(install,dict),'installed_identity_missing'):
            install=obj(install);derived=obj(install.get('derived_build'))
            f['app_id']=text(install.get('bundle_id'));f['build']=text(derived.get('build'))
            f['artifact_sha256']=text(install.get('bundle_manifest_sha256'))
            row.need(install.get('installed_container_verified') is True
                     and install.get('installed_manifest_sha256')==f['artifact_sha256'],'installed_artifact_mismatch')
            # A current-source build always records its reconciliation slot: null when no receipt was needed,
            # otherwise the receipt (checked above). A result without the field has no cleanup proof for the build.
            if 'derived_build' in install and not row.need('derived_transaction_reconciliation' in result,
                                                           'reconciliation_record_missing'):
                cleanup=False
            row.need(derived.get('source_head')==source_head and derived.get('source_build')==f['build'],
                     'build_source_mismatch')
    elif platform=='android':
        android=result.get('android')
        if row.need(isinstance(android,dict),'installed_identity_missing'):
            android=obj(android);app=obj(android.get('app'))
            code=app.get('version_code')
            f['app_id']=text(app.get('package_name'))
            f['build']=str(code) if type(code) is int else None
            f['artifact_sha256']=text(app.get('apk_sha256'));f['source_commit']=text(app.get('source_sha'))
            row.need(app.get('package_name_readback')==f['app_id'] and app.get('version_code_readback')==code
                     and app.get('installed_apk_sha256')==f['artifact_sha256'],'installed_artifact_mismatch')
            row.need(f['source_commit']==source_head,'build_source_mismatch')
            same(row,result.get('android_runtime'),result.get('android_runtime_post_run'),'android_runtime_changed')
            before,after=obj(android.get('device_identity_before')),obj(android.get('device_identity_after'))
            emulator=obj(android.get('emulator_cleanup'))
            row.need(before.get('state')=='absent' and before.get('serial')==device_id,'emulator_not_fresh')
            cleanup=(cleanup and release.get('cleanup') is True and after.get('state')=='absent'
                     and after.get('serial')==device_id and emulator.get('owned_process_absent') is True
                     and emulator.get('owned_process_group_absent') is True and emulator.get('serial_absent') is True)
    row.need(cleanup,'cleanup_not_proven');f['cleanup_proven']=cleanup
    repo_root=text(result.get('repo_root'))
    junit_flows(row,run,result,Path(repo_root) if repo_root else None)
    row.need(result.get('ok') is True and result.get('exit_code')==0,'run_not_ok')
    if any(flow['result']!='PASS' for flow in f['flows']):row.fail('flow_failed')
    check_identity(row,expected_artifact,expected_sha256)
    return row.result()

def split_version_build(value):
    """(version, build) as release_device_qa.parse_version_build reads `1.0 (5)`, `1.0+5` or `1.0-5`."""
    cleaned=value.strip()
    match=re.fullmatch(r'(?P<version>.+?)\s*\((?P<build>[^()]+)\)',cleaned)
    if match:return match.group('version').strip(),match.group('build').strip()
    for mark in ('+','-'):
        if mark in cleaned:
            version,build=cleaned.rsplit(mark,1);return version.strip(),build.strip()
    return cleaned,''

def appium_artifact(row,summary):
    """The installed-artifact digest of an appium run, bound to its device readback."""
    f=row.fields
    f['artifact_sha256']=text(summary.get('installed_artifact_sha256'))
    source=summary.get('installed_artifact_source');f['artifact_source']=text(source)
    if f['artifact_sha256'] is None:return  # check_identity fails the row: artifact_sha256_missing
    if not row.need(source==APPIUM_ARTIFACT_SOURCES.get(str(f['platform'])),'artifact_source_invalid'):return
    readback=summary.get('installed_artifact_readback')
    if not row.need(isinstance(readback,dict),'artifact_readback_missing'):return
    readback=obj(readback)
    version,build=split_version_build(f['build'] or '')
    if source=='installed-split-apks':
        raw_files=readback.get('files')
        files:list[dict[str,object]]=[item for item in raw_files if isinstance(item,dict)] if isinstance(raw_files,list) else []
        valid=(isinstance(raw_files,list) and files and len(files)==len(raw_files) and all(
            isinstance(name:=item.get('name'),str) and name and '\n' not in name and ' ' not in name
            and isinstance(sha:=item.get('sha256'),str) and SHA256.fullmatch(sha)
            and type(size:=item.get('bytes')) is int and size>0 for item in files))
        if not row.need(valid,'artifact_readback_invalid'):return
        pairs=sorted((str(item['name']),str(item['sha256'])) for item in files)
        names=[name for name,_ in pairs]
        lines=''.join(f'{name} {sha}\n' for name,sha in pairs)
        row.need(len(set(names))==len(names) and hashlib.sha256(lines.encode()).hexdigest()==f['artifact_sha256'],
                 'artifact_readback_mismatch')
        row.need(readback.get('package_name')==f['app_id'] and readback.get('version_name')==version
                 and readback.get('version_code')==build,'artifact_identity_mismatch')
    else:
        size=readback.get('ipa_bytes')
        row.need(type(size) is int and size>0 and text(readback.get('device_readback_source')),'artifact_readback_invalid')
        row.need(readback.get('bundle_id')==f['app_id'] and readback.get('version')==version
                 and readback.get('build')==build,'artifact_identity_mismatch')

def appium_row(run,expected_artifact,expected_sha256):
    summary=read_json(run/APPIUM_SUMMARY)
    row=Row('appium');f=row.fields
    platform=summary.get('platform');f['platform']=platform
    device_id=text(summary.get('device_id'));lease_id=text(summary.get('lease_id'))
    if row.need(device_id,'device_missing') and platform in PLATFORMS:f['device_key']=device_key(platform,device_id)
    f['device_name']=device_id  # the lab's logical device ID (e.g. iphone-13-mini), never the UDID or serial
    f['lease_id']=lease_id
    row.need(lease_id,'lease_id_missing')
    f['app_id']=text(summary.get('bundle_id'));f['build']=text(summary.get('version_build'))
    raw_steps=summary.get('steps')
    steps=[step for step in raw_steps if isinstance(step,dict)] if isinstance(raw_steps,list) else []
    flows=[step for step in steps if str(step.get('id','')).startswith(APPIUM_FLOW_PREFIX)]
    f['flows']=[{'flow':step['id'],'result':'PASS' if step.get('ok') is True else 'FAIL'} for step in flows]
    row.need(flows,'flows_missing')
    if any(flow['result']!='PASS' for flow in f['flows']):row.fail('flow_failed')
    row.need(summary.get('ok') is True,'run_not_ok')
    # The runner writes the release step into run-summary.json and lease-release.json; both must agree.
    release_steps=[step for step in steps if step.get('id')=='release_lease']
    try:release=read_json(run/APPIUM_RELEASE)
    except Unreadable:release={}
    row.need(len(release_steps)==1 and release_steps[0]==release,'lease_release_record_mismatch')
    payload=obj(release.get('json'))
    released=(release.get('ok') is True and release.get('exit_code')==0 and payload.get('released')==lease_id
              and payload.get('release_blocked')=='')
    row.need(released,'lease_not_released');f['lease_released']=released
    proof=obj(payload.get('cleanup_proof'))
    listeners=proof.get('listeners');runtime=proof.get('registered_runtime')
    cleanup=(proof.get('cleanup_proven') is True and proof.get('process_observation')=='ok'
             and proof.get('matching_process_count')==0 and isinstance(listeners,dict)
             and all(value is False for value in listeners.values()) and isinstance(runtime,list)
             and all(isinstance(item,dict) and item.get('status') in RUNTIME_ABSENT for item in runtime))
    for step in steps:
        if step.get('id')=='cached_wda_xcodebuild_cleanup':
            cleanup=cleanup and step.get('ok') is True and step.get('remaining_process_count')==0
    row.need(cleanup,'cleanup_not_proven');f['cleanup_proven']=cleanup
    appium_artifact(row,summary)
    check_identity(row,expected_artifact,expected_sha256)
    return row.result()

def validate(run,expected_artifact,expected_sha256=None):
    run=Path(run)
    if (run/MAESTRO_RESULT).is_file():return maestro_row(run,expected_artifact,expected_sha256)
    if (run/APPIUM_SUMMARY).is_file():return appium_row(run,expected_artifact,expected_sha256)
    raise Unreadable('no_run_result')

def with_scenarios(row,catalog):
    """The row with each flow's catalog scenario IDs for the row's platform (maestro-cli flows are repository paths;
    appium flows are not)."""
    flows=[{**flow,'scenarios':[s['id'] for s in catalog['scenarios']
                                if s['maestroFlow']==flow['flow'] and row['platform'] in s['platforms']]
            if row['source']=='maestro-cli' else []} for flow in row['flows']]
    return {**row,'flows':flows}

def main(argv=None):
    parser=argparse.ArgumentParser(description='Validate one maestro-cli or appium QA run and print its evidence row')
    parser.add_argument('run',help='maestro-cli output directory or appium artifact root')
    parser.add_argument('--expected-artifact',required=True,help='expected installed identity (see the module docstring)')
    parser.add_argument('--expected-sha256',help='expected artifact SHA-256, when known before the run')
    parser.add_argument('--catalog',help='the scenario catalog, to name the scenario IDs of each flow')
    args=parser.parse_args(argv)
    if args.expected_sha256 is not None and not SHA256.fullmatch(args.expected_sha256):
        parser.error('--expected-sha256 must be 64 lower-case hex characters')
    try:
        row=validate(args.run,args.expected_artifact,args.expected_sha256)
        if args.catalog:
            catalog=read_json_file(Path(args.catalog));errors=catalog_errors(catalog)
            if errors:raise ContractError(f'{args.catalog}: catalog_invalid: '+'; '.join(errors))
            row=with_scenarios(row,catalog)
    except (Unreadable,ContractError) as error:
        print(json.dumps({'status':'unreadable','code':str(error)}));return 2
    print(json.dumps({'status':'passed' if row['result']=='PASS' else 'failed','row':row},indent=2,sort_keys=True))
    return 0 if row['result']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
