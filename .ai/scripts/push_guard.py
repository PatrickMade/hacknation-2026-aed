"""Harness pre-push guard: one push of the task's own branch to the configured GitHub repository.

    python3 -B .ai/scripts/push_guard.py <remote> <url>      (Git's pre-push lines on stdin)

.ai/hooks/pre-push runs it. The repository comes from .ai/agentic.config.json (`github.repository`,
`github.host`); nothing names a repository, an ID or an account here. Agents merge through the pull request after
an independent review (decision D3), so no push to main is ever needed and no human-review contract is read.

Refused: a remote other than origin; a given or effective push URL (after insteadOf rewriting) for another
repository or host; zero or several refs in one push; tags; deletions; non-branch refs; main (and `baseBranch`
when it is not "auto"); any remote branch other than the checked-out one. Allowed: the checked-out branch under its
own name, as a new branch, a fast-forward or a non-fast-forward update such as --force-with-lease.

The guard reads only local Git state and the config file: no network, no credentials. It imports no project
helper, so a change elsewhere cannot weaken it."""
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG='.ai/agentic.config.json'
REMOTE='origin'
SSH_ALIASES=('personalgit',)  # SSH host aliases (~/.ssh/config) that route to github.com with a chosen key
PROTECTED=('main',)
ZERO='0'*40
SHA=re.compile('[0-9a-f]{40}')
REPOSITORY=re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')
HOSTNAME=re.compile(r'[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+')

class Refused(RuntimeError):pass
def require(value,code):
    if not value:raise Refused(code)

def git(root,*args):
    result=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True)
    return result.stdout.strip() if result.returncode==0 else None

def target(root):
    """(owner/repo, host, protected branch names) from the project config."""
    try:config=json.loads((Path(root)/CONFIG).read_text())
    except (OSError,ValueError):raise Refused('guard_config_invalid')
    github=config.get('github') if isinstance(config,dict) else None
    if not isinstance(github,dict):raise Refused('guard_config_invalid')
    repository,host=github.get('repository'),github.get('host')
    if not (isinstance(repository,str) and REPOSITORY.fullmatch(repository) and not repository.endswith('.git')
            and isinstance(host,str) and HOSTNAME.fullmatch(host)):
        raise Refused('guard_config_invalid')
    base=config.get('baseBranch')
    protected=set(PROTECTED)|({base} if isinstance(base,str) and base and base!='auto' else set())
    return repository.lower(),host,{'refs/heads/'+name.lower() for name in protected}

def repository_of(url,host):
    """owner/repo (lower case) of a URL on the host or an SSH alias of it; None for anything else."""
    path=r'/?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?'
    hosts='|'.join(re.escape(h) for h in (host,*SSH_ALIASES))
    patterns=[r'https://'+re.escape(host)+'/'+path,
              r'(?:git@)?(?:'+hosts+'):'+path,
              r'ssh://(?:git@)?(?:'+hosts+')/'+path]
    for pattern in patterns:
        match=re.fullmatch(pattern,url or '')
        if match:return match.group(1).lower()
    return None

def check(root,remote,url,lines):
    repository,host,protected=target(root)
    require(remote==REMOTE,'push_remote_not_origin')
    require(repository_of(url,host)==repository,'push_repository_mismatch')
    effective=git(root,'remote','get-url','--push',REMOTE)
    require(repository_of(effective,host)==repository,'push_repository_mismatch')
    rows=[line.split() for line in lines.splitlines() if line.strip()]
    require(len(rows)==1 and len(rows[0])==4,'push_refs_ambiguous')
    local_ref,local_sha,remote_ref,remote_sha=rows[0]
    require(not local_ref.startswith('refs/tags/') and not remote_ref.startswith('refs/tags/'),'tag_push_refused')
    require(local_ref!='(delete)' and SHA.fullmatch(local_sha) and local_sha!=ZERO,'branch_delete_refused')
    require(remote_ref.startswith('refs/heads/') and SHA.fullmatch(remote_sha),'branch_ref_required')
    require(remote_ref.lower() not in protected,'protected_branch_push_refused')
    head=git(root,'symbolic-ref','-q','HEAD')
    if not head:raise Refused('not_task_branch')  # detached HEAD: no task branch
    require(head.startswith('refs/heads/') and remote_ref==head and local_ref in (head,'HEAD'),'not_task_branch')
    require(git(root,'rev-parse','--verify','-q',head+'^{commit}')==local_sha,'not_task_branch')
    return {'status':'push_allowed','ref':remote_ref,'head':local_sha}

def main(argv):
    if len(argv)!=3:
        print('usage: push_guard.py <remote> <url>  (refs on stdin)',file=sys.stderr);return 2
    root=Path(git('.','rev-parse','--show-toplevel') or '.')
    try:print(json.dumps(check(root,argv[1],argv[2],sys.stdin.read())))
    except Refused as error:
        print(json.dumps({'status':'rejected','code':str(error)}),file=sys.stderr);return 1
    return 0

if __name__=='__main__':sys.exit(main(sys.argv))
