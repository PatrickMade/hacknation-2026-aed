"""Install, upgrade and check the "apptrick-" edition of the agent skill package.

The edition is generated from a pinned revision of its source collection (named in THIRD_PARTY_NOTICES.md).
Every package skill carries the "apptrick-" prefix; no trace of the source brand remains except the attribution
and the recorded source revision; markers are written and read only in their apptrick- forms.

    python3 -B tools/apptrick_skills.py install --source <checkout> [--revision <sha>] [--project <root>]
                                                [--local-skill <name>]...
    python3 -B tools/apptrick_skills.py check   --source <checkout> [--project <root>]
    python3 -B tools/apptrick_skills.py residue [--project <root>]

The edition carries this tool at <skill root>/apptrick-set-up/scripts/apptrick_skills.py, and the shipped
installer entrypoint install-project-skills.mjs runs it. The source is read only with `git show <revision>:<path>`;
nothing is fetched or executed from it. Lines that must name the source carry the source-rule marker; the residue
check reads every other line of this file like any other file of the edition.

Codex: every package skill outside AUTOMATIC gets an explicit-only agents/openai.yaml sidecar, so only the
automatic entrypoints load implicitly. Local project skills listed in the lock's localSkills (default
LOCAL_SKILLS) may carry the edition prefix; the installer never touches, removes or scans them."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

GENERATOR_VERSION=1
LOCK='.ai/apptrick-skills.lock.json'
LICENSE='.ai/third-party/theyskillit-LICENSE.txt'  # source-rule: the retained license file of the source
SKILL_ROOTS=['.agents/skills','.claude/skills']
SOURCE_REPOSITORY='https://github.com/TH-EY/theyskillit'  # source-rule: recorded source repository
OLD,NEW='they-','apptrick-'  # source-rule: the source prefix and the edition prefix
SOURCE_ROSTER='skills/they-set-up/references/skill-coverage.md'  # source-rule: roster file in the source
SELF='apptrick-set-up/scripts/apptrick_skills.py'
WRAPPER='apptrick-set-up/scripts/install-project-skills.mjs'
SOURCE_RULE='# source-rule'
WORK_PREFIX='.apptrick-skills-'  # staging, backup and failed directories of an interrupted install
# Retired names, markers and storage keys of the collection: renamed like the roster.
RETIRED={'they-auto-implement-issue','they-auto-fix-issue'}  # source-rule: retired names in the source
MARKERS={'they-run-ownership'}  # source-rule: ownership marker in the source
STORAGE={'they-prototype-comments','they-prototype-author'}  # source-rule: storage keys in the source
GENERIC_WORDS={'they-skill'}  # source-rule: generic wording in the source
# Reviewed text rules applied before the token rename (old text, new text). Line counts stay equal.
TEXT_RULES=[
    ('use `they-estimate`,\n`they-fact-check` and `they-prototype-om` directly.',  # source-rule: another collection
     "use the General collection's\nown command names directly."),
    ('THEY.dev','AppTrick'),  # source-rule: brand
    ('a clean THEYskillit source checkout','a clean source collection checkout'),  # source-rule: brand
    ('and requires Node.js and Git. If either is','and requires Node.js, Python 3 and Git. If any of them is'),
    ('.ai/skills.lock.json','.ai/apptrick-skills.lock.json'),
]
# Codex catalog policy: the automatic entrypoints. Every other package skill is explicit-only in Codex.
AUTOMATIC=('apptrick-deliver','apptrick-review','apptrick-verify','apptrick-continue-pr','apptrick-plan',
           'apptrick-set-up','apptrick-upgrade')
CODEX_SIDECAR='agents/openai.yaml'
EXPLICIT=b'policy:\n  allow_implicit_invocation: false\n'
# Local project skills that carry the edition prefix but are not part of the package (decision D1).
LOCAL_SKILLS=('apptrick-template-workflow',)
SKILL_NAME=re.compile(r'apptrick-[a-z0-9-]+')
TOKEN=re.compile(r'(?<![A-Za-z0-9_.])they-[A-Za-z0-9_-]*[A-Za-z0-9_]|(?<![A-Za-z0-9_.])they-(?=[*<\[`])')  # source-rule
# Residue: the source brand in any form. English prose "they"/"They" is not matched; capitals are.
RESIDUE=re.compile(r'(?<![A-Za-z0-9])(?i:they)[-_]|(?<![A-Za-z])THEY|(?i:theyskillit|th-ey|they\.dev)')  # source-rule
DOCS=['README.md','AGENTS.md','CLAUDE.md','SDLC.md','THIRD_PARTY_NOTICES.md','CODE_REVIEW.md','.gitignore','.ai/agentic.config.json']
DOC_GLOBS=['docs/**/*.md','e2e/*.md','.ai/**/*.md','.ai/contracts/*.json','.ai/hooks/*']
# Historical records keep the names they were written with; the residue check does not read them.
HISTORY=('.ai/specs/','.ai/runs/')
ALLOWED=[LICENSE,'"sourceRepository": "'+SOURCE_REPOSITORY+'"']  # exact substrings removed before matching
ATTRIBUTION_PREFIX='- Skill package attribution:'  # the one attribution line in THIRD_PARTY_NOTICES.md
WRAPPER_TEXT='''#!/usr/bin/env node
// apptrick- edition installer: the shipped command line, running the bundled transform.
//   node install-project-skills.mjs --source <checkout> --project <root> [--check] [--revision <sha>]
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const args = process.argv.slice(2)
const check = args.includes('--check')
const rest = args.filter((value) => value !== '--check')
const tool = path.join(path.dirname(fileURLToPath(import.meta.url)), 'apptrick_skills.py')
const result = spawnSync('python3', ['-B', tool, check ? 'check' : 'install', ...rest], { stdio: 'inherit' })
if (result.error) console.error(`apptrick installer: cannot run python3 (${result.error.message})`)
else if (result.status === null) console.error(`apptrick installer: transform stopped by signal ${result.signal}`)
process.exit(result.status === null ? 1 : result.status)
'''

class Refused(RuntimeError):pass
def require(value,code):
    if not value:raise Refused(code)
def sha256(data):return hashlib.sha256(data).hexdigest()

def git_bytes(source,*args):
    result=subprocess.run(['git','-C',str(source),*args],capture_output=True)
    require(result.returncode==0,'source_git_failed:'+' '.join(args[:2]))
    return result.stdout
def git(source,*args):return git_bytes(source,*args).decode()

def roster(source,revision):
    text=git(source,'show',revision+':'+SOURCE_ROSTER)
    match=re.search(r'^ROSTER="([^"]+)"$',text,re.M)
    if match is None:raise Refused('source_roster_missing')
    names=match.group(1).split();require(len(names)==len(set(names)) and all(n.startswith(OLD) for n in names),'source_roster_invalid')
    return set(names)

def unsafe_parts(path):
    """A relative path with an empty, '.' or '..' part (or an absolute one) could leave its skill directory."""
    return any(part in ('','.','..') for part in path.split('/'))

def rename_text(text,names,where):
    for old,new in TEXT_RULES:
        require(old.count('\n')==new.count('\n'),'text_rule_line_count')
        text=text.replace(old,new)
    renamed=names|RETIRED|MARKERS|STORAGE|GENERIC_WORDS
    def token(match):
        value=match.group(0)
        if value==OLD or value in renamed:return NEW+value[len(OLD):]
        raise Refused('unreviewed_source_token:'+value+':'+where)
    out=TOKEN.sub(token,text)
    before,after=text.splitlines(),out.splitlines()
    require(len(before)==len(after),'rename_changed_line_count:'+where)
    for old_line,new_line in zip(before,after):
        if re.match(r'\s*(PR|Issue|Spec):',old_line):require(old_line==new_line,'marker_line_changed:'+where)
        require(re.findall(r'https?://\S+',old_line)==re.findall(r'https?://\S+',new_line),'url_changed:'+where)
    return out

def explicit_metadata(original,where):
    """The Codex sidecar: the package's own metadata, if any, followed by the explicit-only policy."""
    require(not re.search(rb'^policy\s*:',original,re.M),'source_codex_policy_present:'+where)
    return original+(b'\n' if original and not original.endswith(b'\n') else b'')+EXPLICIT

def residue_hits(text,where,self_file=False):
    """Every source-brand occurrence outside the explicit allowlist."""
    hits=[]
    for number,line in enumerate(text.splitlines(),1):
        if where.endswith('THIRD_PARTY_NOTICES.md') and line.startswith(ATTRIBUTION_PREFIX):continue
        if self_file and (line.rstrip().endswith(SOURCE_RULE) or SOURCE_RULE+':' in line):continue
        cleaned=line
        for allowed in ALLOWED:cleaned=cleaned.replace(allowed,'')
        for match in RESIDUE.finditer(cleaned):hits.append(f'{where}:{number}:{match.group(0)}')
    return hits

def generate(source,revision,tool_bytes=None,automatic=AUTOMATIC,local=LOCAL_SKILLS):
    """{relative path under a skill root: (bytes, mode)} for the apptrick- edition at the given revision."""
    names=roster(source,revision)
    listing=git(source,'ls-tree','-r','-z',revision,'--','skills')
    files={}
    for entry in listing.split('\0'):
        if not entry:continue
        meta,path=entry.split('\t',1);mode,kind,_=meta.split()
        require(kind=='blob' and mode in ('100644','100755'),'source_entry_unsupported:'+path)
        parts=path.split('/');require(not unsafe_parts(path),'source_path_unsafe:'+path)
        require(len(parts)>2 and parts[0]=='skills' and parts[1] in names,'source_skill_unknown:'+path)
        data=git_bytes(source,'show',revision+':'+path)
        try:text=data.decode('utf-8')
        except UnicodeDecodeError:text=None
        if text is not None:data=rename_text(text,names,path).encode('utf-8')
        target='/'.join([NEW+parts[1][len(OLD):]]+parts[2:])
        files[target]=(data,0o755 if mode=='100755' else 0o644)
    require(WRAPPER in files,'source_installer_missing')
    files[WRAPPER]=(WRAPPER_TEXT.encode(),0o755)
    files[SELF]=(tool_bytes if tool_bytes is not None else Path(__file__).resolve().read_bytes(),0o755)
    skills={p.split('/')[0] for p in files}
    invalid=sorted(n for n in skills if not SKILL_NAME.fullmatch(n))
    require(not invalid,'generated_skill_name_invalid:'+','.join(invalid))
    require(len(skills)==len(names),'generated_roster_incomplete')
    require(len(set(automatic))==len(automatic) and set(automatic)<=skills,'codex_automatic_unknown')
    require(not set(local)&skills,'local_skill_collides:'+','.join(sorted(set(local)&skills)))
    for name in sorted(skills-set(automatic)):
        sidecar=name+'/'+CODEX_SIDECAR
        original,mode=files.get(sidecar,(b'',0o644))
        files[sidecar]=(explicit_metadata(original,sidecar),mode)
    for target,(data,_) in files.items():
        if target.endswith('/SKILL.md'):
            name=re.search(r'^name: (\S+)$',data.decode(),re.M)
            require(name is not None and name.group(1)==target.split('/')[0],'generated_frontmatter_mismatch:'+target)
        try:hits=residue_hits(data.decode('utf-8'),target,self_file=(target==SELF))
        except UnicodeDecodeError:hits=[]
        require(not hits,'generated_residue:'+(hits[0] if hits else ''))
    return files,names

def expected_lock(source,revision,files,automatic=AUTOMATIC,local=LOCAL_SKILLS):
    return {'schemaVersion':1,'edition':'apptrick','sourceRepository':SOURCE_REPOSITORY,'sourceRevision':revision,
            'sourceLicenseSha256':sha256(git_bytes(source,'show',revision+':LICENSE')),
            'generator':{'path':'<skill root>/'+SELF,'version':GENERATOR_VERSION,'sha256':sha256(files[SELF][0])},
            'skillRoots':SKILL_ROOTS,'skills':sorted({p.split('/')[0] for p in files}),
            'localSkills':sorted(local),
            'codexCatalog':{'version':1,'automatic':sorted(automatic),
                            'explicitOnly':sorted(p for p in files if p.endswith('/'+CODEX_SIDECAR) and p.count('/')==2)},
            'files':{p:sha256(data) for p,(data,_) in sorted(files.items())},
            'executables':sorted(p for p,(_,mode) in files.items() if mode&0o111)}

def installed(base,skills):
    """{relative path: (bytes, mode)} of the given skill directories in one root."""
    out={}
    for name in skills:
        directory=Path(base)/name
        if not directory.is_dir():continue
        for path in directory.rglob('*'):
            require(not path.is_symlink(),'skill_symlink_refused:'+str(path))
            if path.is_file():out[path.relative_to(base).as_posix()]=(path.read_bytes(),path.stat().st_mode&0o777)
    return out

def matches_lock(root,lock):
    """The installed package equals a lock in both roots: file set, hashes and executable bits."""
    for skill_root in lock['skillRoots']:
        tree=installed(Path(root)/skill_root,lock['skills'])
        require({p:sha256(d) for p,(d,_) in tree.items()}==lock['files'],'installed_package_differs_from_lock:'+skill_root)
        if 'executables' in lock:
            require({p for p,(_,mode) in tree.items() if mode&0o111}==set(lock['executables']),'installed_modes_differ_from_lock:'+skill_root)

def doc_paths(root):
    root=Path(root)
    paths=[root/p for p in DOCS]+[p for pattern in DOC_GLOBS for p in sorted(root.glob(pattern)) if p.is_file()]
    return [p for p in paths if not p.relative_to(root).as_posix().startswith(HISTORY)]

def residue(root,edition=None,local=LOCAL_SKILLS):
    """Source-brand residue in the installed edition (or a given generated one) and the repository docs.
    Local project skills and the historical records under HISTORY are not part of the scope."""
    root=Path(root);hits=[]
    if edition is None:
        for skill_root in SKILL_ROOTS:
            base=root/skill_root
            if not base.is_dir():continue
            for directory in sorted(p for p in base.iterdir() if p.name.startswith((OLD,NEW)) and p.name not in local):
                for path in sorted(directory.rglob('*')):
                    if not path.is_file():continue
                    rel=path.relative_to(base).as_posix()
                    try:text=path.read_text()
                    except UnicodeDecodeError:continue
                    hits+=residue_hits(text,skill_root+'/'+rel,self_file=(rel==SELF))
    for path in doc_paths(root):
        if path.is_file():hits+=residue_hits(path.read_text(),path.relative_to(root).as_posix())
    if (root/LOCK).is_file():hits+=residue_hits((root/LOCK).read_text(),LOCK)
    return hits

def check_installed(root,files,lock_value):
    root=Path(root);local=set(lock_value['localSkills'])
    lock_path=root/LOCK;require(lock_path.is_file(),'apptrick_lock_missing')
    require(json.loads(lock_path.read_text())==lock_value,'apptrick_lock_drift')
    skills={p.split('/')[0] for p in files}
    for skill_root in SKILL_ROOTS:
        base=root/skill_root
        for entry in base.iterdir():
            require(not entry.name.startswith(WORK_PREFIX),'interrupted_install_leftover:'+skill_root+'/'+entry.name)
            require(not entry.name.startswith(OLD),'source_named_skill_remains:'+skill_root+'/'+entry.name)
            require(not entry.name.startswith(NEW) or entry.name in skills or entry.name in local,'unexpected_apptrick_skill:'+skill_root+'/'+entry.name)
        for name in skills:
            directory=base/name;require(directory.is_dir() and not directory.is_symlink(),'apptrick_skill_missing:'+skill_root+'/'+name)
        tree=installed(base,skills)
        for name in skills:
            wanted={p for p in files if p.split('/')[0]==name};actual={p for p in tree if p.split('/')[0]==name}
            require(actual==wanted,'apptrick_skill_files_differ:'+skill_root+'/'+name)
        for rel,(data,mode) in files.items():
            require(tree[rel][0]==data,'apptrick_file_drift:'+skill_root+'/'+rel)
            require(bool(tree[rel][1]&0o111)==bool(mode&0o111),'apptrick_mode_drift:'+skill_root+'/'+rel)
    license_path=root/LICENSE
    require(license_path.is_file() and sha256(license_path.read_bytes())==lock_value['sourceLicenseSha256'],'license_differs_from_source')
    hits=residue(root,local=local);require(not hits,'residue:'+(hits[0] if hits else ''))
    return len(files)

def atomic_write(path,data,mode=0o644):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:temporary.write_bytes(data);os.chmod(temporary,mode);os.replace(temporary,path)
    except BaseException:
        temporary.unlink(missing_ok=True);raise

def validate_previous(previous,local):
    """The previous lock decides what an install may replace or remove, so it is checked before it is trusted:
    only edition-prefixed skill directories in the edition's roots, never an allowlisted local skill (D1), and
    file paths that stay inside their skill directory."""
    require(isinstance(previous,dict),'previous_lock_invalid:not_an_object')
    require(previous.get('skillRoots')==SKILL_ROOTS,'previous_lock_invalid:skillRoots')
    skills=previous.get('skills');files=previous.get('files');executables=previous.get('executables',[])
    require(isinstance(skills,list) and all(isinstance(n,str) and SKILL_NAME.fullmatch(n) for n in skills),'previous_lock_invalid:skills')
    managed=sorted(set(skills)&set(local))
    require(not managed,'local_skill_managed_by_lock:'+','.join(managed))
    require(isinstance(files,dict) and isinstance(executables,list),'previous_lock_invalid:files')
    for path in list(files)+executables:
        require(isinstance(path,str) and not unsafe_parts(path) and path.split('/')[0] in skills,'previous_lock_invalid:path:'+str(path))

def preflight(root,files,lock_value,previous):
    """Every refusal happens here, before anything in the project changes."""
    root=Path(root);new_skills={p.split('/')[0] for p in files};local=set(lock_value['localSkills'])
    if previous:
        validate_previous(previous,local)
        matches_lock(root,previous)  # edited, missing or extra managed files refuse at any revision
    known=set(previous['skills']) if previous else set()
    for skill_root in SKILL_ROOTS:
        base=root/skill_root
        if not base.is_dir():continue
        for entry in base.iterdir():
            require(not entry.name.startswith(WORK_PREFIX),'interrupted_install_leftover:'+skill_root+'/'+entry.name)
            if not entry.name.startswith((OLD,NEW)) or entry.name in known or entry.name in local:continue
            # Not managed by the previous lock: refused, except on a first install, which adopts an identical copy.
            require(not previous and entry.name in new_skills and entry.is_dir() and not entry.is_symlink(),'unknown_skill_directory:'+skill_root+'/'+entry.name)
            tree={p:d for p,(d,_) in installed(base,[entry.name]).items()}
            require(tree=={p:d for p,(d,_) in files.items() if p.split('/')[0]==entry.name},'unknown_skill_directory:'+skill_root+'/'+entry.name)
    hits=residue(root,edition=files,local=local);require(not hits,'residue:'+(hits[0] if hits else ''))
    license_path=root/LICENSE
    require(not license_path.exists() or sha256(license_path.read_bytes())==lock_value['sourceLicenseSha256'],'license_differs_from_source')

def swap(root,files,remove,commit,fail_after=None):
    """Write the new tree to a staging directory in each root, swap it in skill by skill across both roots, then
    run commit() (the license and lock writes). Backups are deleted only after commit() succeeds; on any failure
    each swapped-in skill is first renamed aside, then its backup renamed back, so a partial delete cannot block
    a restore. fail_after injects a failure after that many swaps (tests only)."""
    root=Path(root);token=uuid.uuid4().hex
    names=sorted(set(remove)|{p.split('/')[0] for p in files})
    stagings=[];backups=[];placed=[]
    try:
        for skill_root in SKILL_ROOTS:
            base=root/skill_root;base.mkdir(parents=True,exist_ok=True)
            staging=base/(WORK_PREFIX+'staging-'+token);staging.mkdir();stagings.append(staging)
            for rel,(data,mode) in sorted(files.items()):
                path=staging/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);os.chmod(path,mode)
        count=0
        for skill_root,staging in zip(SKILL_ROOTS,stagings):
            base=root/skill_root
            for name in names:
                if fail_after is not None and count==fail_after:raise OSError('injected swap failure')
                current=base/name
                if current.exists() or current.is_symlink():
                    backup=base/(WORK_PREFIX+'backup-'+token+'-'+name);os.rename(current,backup);backups.append((backup,current))
                if (staging/name).exists():os.rename(staging/name,current);placed.append(current)
                count+=1
        if fail_after is not None and count==fail_after:raise OSError('injected swap failure')
        commit()
    except BaseException:
        aside=[]
        for path in reversed(placed):
            moved=path.with_name(WORK_PREFIX+'failed-'+token+'-'+path.name);os.rename(path,moved);aside.append(moved)
        for backup,current in reversed(backups):os.rename(backup,current)
        for path in aside+stagings:shutil.rmtree(path,ignore_errors=True)
        raise
    for backup,_ in backups:
        if backup.is_dir() and not backup.is_symlink():shutil.rmtree(backup)
        else:backup.unlink()
    for staging in stagings:shutil.rmtree(staging)

def install(root,source,files,lock_value,previous,fail_after=None):
    root=Path(root);local=set(lock_value['localSkills'])
    preflight(root,files,lock_value,previous)
    if previous==lock_value and (root/LICENSE).is_file():
        return check_installed(root,files,lock_value)  # same revision and tree: nothing to write
    remove=set(previous['skills']) if previous else set()
    remove|={p.name for skill_root in SKILL_ROOTS if (root/skill_root).is_dir() for p in (root/skill_root).iterdir()
             if p.name.startswith((OLD,NEW)) and p.name not in local}
    license_body=git_bytes(source,'show',lock_value['sourceRevision']+':LICENSE')
    license_existed=(root/LICENSE).is_file()  # the preflight proved an existing license already equals this body
    def commit():
        try:
            atomic_write(root/LICENSE,license_body)
            atomic_write(root/LOCK,(json.dumps(lock_value,indent=2)+'\n').encode())  # last step: the old lock stays on any failure
        except BaseException:
            if not license_existed:(root/LICENSE).unlink(missing_ok=True)
            raise
    swap(root,files,remove,commit,fail_after)
    return check_installed(root,files,lock_value)

def main(argv=None):
    parser=argparse.ArgumentParser(description='apptrick- edition of the agent skill package')
    parser.add_argument('action',choices=['install','check','residue'])
    parser.add_argument('--source',help='a clean checkout of the source collection (read with git show only)')
    parser.add_argument('--revision',help='source revision; defaults to the pinned one, then the checkout HEAD')
    parser.add_argument('--project',default='.')
    parser.add_argument('--local-skill',action='append',dest='local_skills',metavar='NAME',
                        help='a local project skill that may carry the edition prefix (repeatable); '
                             'defaults to the lock\'s localSkills, then '+', '.join(LOCAL_SKILLS))
    args=parser.parse_args(argv)
    root=Path(args.project).resolve()
    try:
        previous=json.loads((root/LOCK).read_text()) if (root/LOCK).is_file() else None
        require(previous is None or isinstance(previous,dict),'previous_lock_invalid:not_an_object')
        if args.local_skills:local=tuple(args.local_skills)
        elif previous and previous.get('localSkills') is not None:local=tuple(previous['localSkills'])  # an empty list stays empty
        else:local=LOCAL_SKILLS
        require(all(isinstance(name,str) and SKILL_NAME.fullmatch(name) for name in local),'local_skill_invalid')
        if args.action=='residue':
            hits=residue(root,local=local);require(not hits,'residue:'+'; '.join(hits[:20]))
            print(json.dumps({'status':'clean'}));return 0
        require(args.source,'source_required')
        source=Path(args.source).resolve()
        pinned=previous.get('sourceRevision') if previous else None
        revision=args.revision or pinned or git(source,'rev-parse','HEAD').strip()
        require(re.fullmatch('[0-9a-f]{40}',revision or ''),'source_revision_required')
        require(args.action=='install' or revision==pinned,'check_uses_the_pinned_revision')
        files,_=generate(source,revision,local=local);lock_value=expected_lock(source,revision,files,local=local)
        count=install(root,source,files,lock_value,previous) if args.action=='install' else check_installed(root,files,lock_value)
    except Refused as error:
        print(json.dumps({'status':'rejected','code':str(error)}),file=sys.stderr);return 1
    print(json.dumps({'status':'installed' if args.action=='install' else 'verified','revision':revision,'files':count,'roots':SKILL_ROOTS}))
    return 0

if __name__=='__main__':sys.exit(main())
