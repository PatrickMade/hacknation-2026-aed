"""Check an installed project against its harness lock (.ai/harness.lock.json).

    python3 -B .ai/scripts/check_harness.py [--project <root>]

It verifies four things without the upstream source or the network:

1. The edition: .ai/apptrick-skills.lock.json is the file the harness lock pins, and both skill roots hold exactly
   the locked package files with their hashes and executable bits. A skill directory with the edition prefix that is
   neither locked nor an allowlisted local skill, or an interrupted-install leftover, refuses.
2. The harness files: every path in `files` (hooks, scripts, notices) has its pinned SHA-256, the executable set
   matches, and .ai/hooks and .ai/third-party hold no unlisted file. An extension (.ai/skills/<name>/SKILL.md) is
   pinned only by its harness-owned block, the bytes between the `<!-- apptrick-harness:begin -->` and
   `<!-- apptrick-harness:end -->` lines (`blocks`), which hold the core rules followed by the rules of each installed
   overlay; the app may add rules outside the block and other files in .ai/skills (an installed skill appends to its
   repo-local skill there). Each pinned extension extends an installed edition skill of the same name.
3. The Linear config block: `linear` and `ticketKeyPattern` in .ai/agentic.config.json pass the adapter's own
   validation, and the scope values (workspace, team, states, template and lab routes, key pattern, set by an overlay
   or, without one, by the app) hash to the pinned `linearSha256`. `linear.project` and `linear.routing.app` are not
   pinned.
4. The overlays: `harness.overlays` in .ai/agentic.config.json equals the overlays the lock was installed with
   (`harness.overlays` of the lock). Changing the list needs a new install.

The harness installer (tools/install_harness.py in the harness repository) writes the lock with expected_lock().
Prints one JSON object; exit 0 passed, 1 rejected."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import apptrick_linear  # noqa: E402  (installed next to this file)

LOCK='.ai/harness.lock.json'
EDITION_LOCK='.ai/apptrick-skills.lock.json'
CONFIG='.ai/agentic.config.json'
SKILL_ROOTS=['.agents/skills','.claude/skills']
EXTENSIONS='.ai/skills'
CLOSED_ROOTS=['.ai/hooks','.ai/third-party']  # every file here must be in the lock; .ai/skills stays open
BEGIN_MARK=b'<!-- apptrick-harness:begin -->'
END_MARK=b'<!-- apptrick-harness:end -->'
EDITION_PREFIX='apptrick-'
WORK_PREFIX='.apptrick-skills-'
LOCK_KEYS={'schemaVersion','harness','editionLockSha256','files','blocks','executables','linearSha256'}
LINEAR_OWNED=('workspace','team','teamId','states')
APP_ROUTE='app'
HARNESS_KEYS={'repository','revision','overlays'}
OVERLAY_NAME=re.compile('[a-z0-9][a-z0-9-]*')
DIGEST=re.compile('[0-9a-f]{64}')
REVISION=re.compile('[0-9a-f]{40}')

class Rejected(RuntimeError):pass
def require(value,code):
    if not value:raise Rejected(code)
def digest(data):return hashlib.sha256(data).hexdigest()

def safe_path(root,rel):
    """root/rel for a plain relative path with no symlink on the way."""
    require(isinstance(rel,str) and rel and not rel.startswith('/') and '\\' not in rel
            and all(part not in ('','.','..') for part in rel.split('/')),'unsafe_path:'+str(rel))
    path=Path(root)
    for part in rel.split('/'):
        path=path/part
        require(not path.is_symlink(),'symlink_refused:'+rel)
    return path

def read_json(root,rel):
    path=safe_path(root,rel)
    require(path.is_file(),'missing:'+rel)
    try:return json.loads(path.read_text())
    except ValueError:raise Rejected('invalid_json:'+rel)

def linear_digest(config):
    """SHA-256 of the harness-owned Linear values of a parsed .ai/agentic.config.json."""
    linear=config['linear']
    owned={key:linear[key] for key in LINEAR_OWNED}
    owned['routing']={k:v for k,v in linear['routing'].items() if k!=APP_ROUTE}
    owned['ticketKeyPattern']=config['ticketKeyPattern']
    return digest(json.dumps(owned,sort_keys=True,separators=(',',':')).encode())

def strings(value):return isinstance(value,list) and all(isinstance(item,str) for item in value)
def overlay_list(value):
    return strings(value) and len(set(value))==len(value) and all(OVERLAY_NAME.fullmatch(item) for item in value)

def config_overlays(config):
    """`harness.overlays` of a parsed .ai/agentic.config.json: the overlay names the project installs, in order."""
    harness=config.get('harness') if isinstance(config,dict) else None
    overlays=harness.get('overlays') if isinstance(harness,dict) else None
    require(overlay_list(overlays),'harness_overlays_invalid')
    return overlays
def digests(value):
    return isinstance(value,dict) and all(isinstance(k,str) and isinstance(v,str) and DIGEST.fullmatch(v) for k,v in value.items())

def harness_block(data,rel):
    """The bytes between the one begin-marker line and the one end-marker line after it."""
    lines=data.split(b'\n')
    begins=[i for i,line in enumerate(lines) if line==BEGIN_MARK]
    ends=[i for i,line in enumerate(lines) if line==END_MARK]
    require(len(begins)==1 and len(ends)==1 and begins[0]<ends[0],'harness_block_markers:'+rel)
    return b'\n'.join(lines[begins[0]+1:ends[0]])

def tree(base):
    """{path relative to base: (bytes, executable)} of every file below base; symlinks refuse."""
    out={}
    for path in sorted(base.rglob('*')):
        require(not path.is_symlink(),'symlink_refused:'+path.as_posix())
        if path.is_file():out[path.relative_to(base).as_posix()]=(path.read_bytes(),bool(path.stat().st_mode&0o111))
    return out

def check_edition(root,lock):
    edition=read_json(root,EDITION_LOCK)
    require(digest(safe_path(root,EDITION_LOCK).read_bytes())==lock['editionLockSha256'],'edition_lock_drift')
    require(isinstance(edition,dict) and edition.get('skillRoots')==SKILL_ROOTS,'edition_lock_invalid')
    skills,files=edition.get('skills'),edition.get('files')
    local,executables=edition.get('localSkills',[]),edition.get('executables',[])
    if not (strings(skills) and digests(files) and strings(local) and strings(executables)):
        raise Rejected('edition_lock_invalid')
    assert isinstance(skills,list) and isinstance(files,dict) and isinstance(local,list) and isinstance(executables,list)
    for skill_root in SKILL_ROOTS:
        base=safe_path(root,skill_root)
        require(base.is_dir(),'edition_root_missing:'+skill_root)
        for entry in sorted(base.iterdir()):
            require(not entry.name.startswith(WORK_PREFIX),'interrupted_install_leftover:'+skill_root+'/'+entry.name)
            require(not entry.name.startswith(EDITION_PREFIX) or entry.name in skills or entry.name in local,
                    'unexpected_edition_skill:'+skill_root+'/'+entry.name)
        installed={}
        for name in skills:
            directory=safe_path(root,skill_root+'/'+name)
            require(directory.is_dir(),'edition_skill_missing:'+skill_root+'/'+name)
            installed.update({name+'/'+rel:value for rel,value in tree(directory).items()})
        for rel in sorted(set(files)|set(installed)):
            require(rel in installed and rel in files,'edition_files_differ:'+skill_root+'/'+rel)
            require(digest(installed[rel][0])==files[rel],'edition_file_drift:'+skill_root+'/'+rel)
            require(installed[rel][1]==(rel in executables),'edition_mode_drift:'+skill_root+'/'+rel)
    return set(skills),len(files)*len(SKILL_ROOTS)

def is_extension(rel):
    parts=rel.split('/')
    return rel.startswith(EXTENSIONS+'/') and len(parts)==4 and parts[3]=='SKILL.md'

def check_files(root,lock,skills):
    files,blocks,executables=lock['files'],lock['blocks'],lock['executables']
    require(digests(files) and digests(blocks) and strings(executables) and set(executables)<=set(files),'harness_lock_invalid')
    require(not any(rel.startswith(EXTENSIONS+'/') for rel in files) and all(is_extension(rel) for rel in blocks),
            'harness_lock_invalid')
    for rel,pinned in sorted(files.items()):
        path=safe_path(root,rel)
        require(path.is_file(),'harness_file_missing:'+rel)
        require(digest(path.read_bytes())==pinned,'harness_drift:'+rel)
        require(bool(path.stat().st_mode&0o111)==(rel in executables),'harness_mode_drift:'+rel)
    for rel,pinned in sorted(blocks.items()):
        path=safe_path(root,rel)
        require(rel.split('/')[2] in skills,'extension_without_skill:'+rel)
        require(path.is_file(),'harness_file_missing:'+rel)
        require(digest(harness_block(path.read_bytes(),rel))==pinned,'harness_block_drift:'+rel)
    for closed in CLOSED_ROOTS:
        base=safe_path(root,closed)
        if not base.exists():continue
        for rel in tree(base):
            require(closed+'/'+rel in files,'unvetted_harness_file:'+closed+'/'+rel)
    return len(files)+len(blocks)

def check_linear(root,lock):
    config=read_json(root,CONFIG)
    try:apptrick_linear.load_config(safe_path(root,CONFIG))
    except apptrick_linear.AdapterError as error:raise Rejected('linear_config_invalid:'+str(error))
    require(linear_digest(config)==lock['linearSha256'],'linear_config_drift')

def check_overlays(root,lock):
    require(config_overlays(read_json(root,CONFIG))==lock['harness']['overlays'],'overlays_drift')

def check(root,installing=False):
    """`installing` is the installer's check of the installed state before it writes: it also accepts a lock written
    before overlays existed (no `harness.overlays`) and leaves the overlay list and the Linear block to the install,
    which may change both and validates and pins the result."""
    root=Path(root)
    lock=read_json(root,LOCK)
    require(isinstance(lock,dict) and set(lock)==LOCK_KEYS and lock['schemaVersion']==1,'harness_lock_invalid')
    harness=lock['harness']
    allowed=[HARNESS_KEYS]+([HARNESS_KEYS-{'overlays'}] if installing else [])
    require(isinstance(harness,dict) and set(harness) in allowed
            and isinstance(harness['repository'],str) and harness['repository'].startswith('https://')
            and isinstance(harness['revision'],str) and REVISION.fullmatch(harness['revision'])
            and ('overlays' not in harness or overlay_list(harness['overlays'])),'harness_lock_invalid')
    require(all(isinstance(lock[k],str) and DIGEST.fullmatch(lock[k]) for k in ('editionLockSha256','linearSha256')),
            'harness_lock_invalid')
    skills,edition=check_edition(root,lock)
    files=check_files(root,lock,skills)
    if not installing:
        check_linear(root,lock)
        check_overlays(root,lock)
    return {'status':'passed','revision':harness['revision'],'overlays':harness.get('overlays'),'editionFiles':edition,
            'harnessFiles':files,'linear':'pinned'}

def expected_lock(root,repository,revision,paths):
    """The lock for a project as it stands: the installer calls it after installing `paths` (project paths).
    Extensions (.ai/skills/<name>/SKILL.md) are pinned by their harness block, every other path by its bytes; the
    overlays are the config's `harness.overlays`."""
    root=Path(root);plain=[rel for rel in paths if not is_extension(rel)];extensions=[rel for rel in paths if is_extension(rel)]
    config=read_json(root,CONFIG)
    return {'schemaVersion':1,'harness':{'repository':repository,'revision':revision,'overlays':config_overlays(config)},
            'editionLockSha256':digest(safe_path(root,EDITION_LOCK).read_bytes()),
            'files':{rel:digest(safe_path(root,rel).read_bytes()) for rel in sorted(plain)},
            'blocks':{rel:digest(harness_block(safe_path(root,rel).read_bytes(),rel)) for rel in sorted(extensions)},
            'executables':sorted(rel for rel in plain if safe_path(root,rel).stat().st_mode&0o111),
            'linearSha256':linear_digest(config)}

def main(argv=None):
    parser=argparse.ArgumentParser(description='Check an installed project against .ai/harness.lock.json')
    parser.add_argument('--project',default='.')
    args=parser.parse_args(argv)
    try:result=check(Path(args.project).resolve())
    except (Rejected,OSError,KeyError,TypeError,AttributeError) as error:
        code=str(error) if isinstance(error,Rejected) else type(error).__name__
        print(json.dumps({'status':'rejected','code':code}));return 1
    print(json.dumps(result));return 0

if __name__=='__main__':sys.exit(main())
