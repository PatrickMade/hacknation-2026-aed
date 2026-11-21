"""Check the pinned client configuration hashes in .ai/client-config.json, or refresh one pin.

    python3 -B .ai/scripts/check_client_config.py [--project <root>]
    python3 -B .ai/scripts/check_client_config.py [--project <root>] --update <path>

The project pins its agent instruction files there (`files`: path -> SHA-256). AGENTS.md and CLAUDE.md must be
pinned, and every pinned file must exist as a regular file with its pinned hash. A changed file refuses until the
reviewed change updates its pin in the same pull request.

`--update <path>` is that update: it rewrites only the pin of one already pinned file to the file's current SHA-256
and leaves every other byte of .ai/client-config.json as it is. It never adds or removes a pin. Run it after the
reviewed edit (for example a new gate line in AGENTS.md), then run the check.

This is the digest check only. The full client-file inventory (undeclared files under .agents, .claude and
.codex, personal settings) stays with the edition's check-project-config.mjs. Prints one JSON object; exit 0 passed
(or updated, or unchanged), 1 rejected."""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_harness import DIGEST, Rejected, digest, read_json, require, safe_path  # noqa: E402

CLIENT_CONFIG='.ai/client-config.json'
REQUIRED=('AGENTS.md','CLAUDE.md')

def load(root):
    config=read_json(root,CLIENT_CONFIG)
    require(isinstance(config,dict) and config.get('version')==1 and isinstance(config.get('files'),dict),
            'client_config_invalid')
    return config

def check(root):
    files=load(root)['files']
    for rel in REQUIRED:require(rel in files,'client_config_unpinned:'+rel)
    for rel,pinned in sorted(files.items()):
        require(isinstance(pinned,str) and DIGEST.fullmatch(pinned),'client_config_invalid')
        path=safe_path(root,rel)
        require(path.is_file(),'client_config_missing:'+rel)
        require(digest(path.read_bytes())==pinned,'client_config_drift:'+rel)
    return {'status':'passed','pinned':len(files)}

def update(root,rel):
    """Rewrite the pin of one pinned file to its current SHA-256, as a text edit of that one value."""
    config=load(root);files=config['files']
    require(rel in files,'client_config_unpinned:'+str(rel))
    previous=files[rel]
    require(isinstance(previous,str) and DIGEST.fullmatch(previous),'client_config_invalid')
    path=safe_path(root,rel)
    require(path.is_file(),'client_config_missing:'+rel)
    current=digest(path.read_bytes())
    if current==previous:return {'status':'unchanged','path':rel,'sha256':current}
    manifest=safe_path(root,CLIENT_CONFIG);text=manifest.read_text()
    pin=re.compile(re.escape(json.dumps(rel))+r'(\s*:\s*)"'+previous+'"')
    require(len(pin.findall(text))==1,'client_config_pin_not_unique:'+rel)
    rewritten=pin.sub(lambda match:json.dumps(rel)+match.group(1)+'"'+current+'"',text)
    # The edit must change exactly that one value: everything else parses back unchanged.
    require(json.loads(rewritten)==dict(config,files=dict(files,**{rel:current})),'client_config_rewrite_mismatch:'+rel)
    temporary=manifest.with_name(manifest.name+'.update');temporary.write_text(rewritten);os.replace(temporary,manifest)
    return {'status':'updated','path':rel,'previous':previous,'sha256':current}

def main(argv=None):
    parser=argparse.ArgumentParser(description='Check the pinned hashes in .ai/client-config.json, or refresh one pin')
    parser.add_argument('--project',default='.')
    parser.add_argument('--update',metavar='PATH',help='rewrite only the pin of this pinned file to its current hash')
    args=parser.parse_args(argv)
    root=Path(args.project).resolve()
    try:result=update(root,args.update) if args.update is not None else check(root)
    except (Rejected,OSError,AttributeError,TypeError,ValueError) as error:
        code=str(error) if isinstance(error,Rejected) else type(error).__name__
        print(json.dumps({'status':'rejected','code':code}));return 1
    print(json.dumps(result));return 0

if __name__=='__main__':sys.exit(main())
