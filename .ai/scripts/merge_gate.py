"""The merge gate: refuse a PR merge unless the review, the required checks and the QA verdicts are on its head.

    python3 -B .ai/scripts/merge_gate.py --pr <number> [--project <root>] [--author-session <id>] [--strict]
        [--merge --author-session <id>]

Run it from the project checkout, with `gh` signed in to the account the project's runs use and the PR head
fetched. It reads the PR and its comparison with the base through `gh`, the project config
(.ai/agentic.config.json) and the local Git history. It refuses when any of these fails:

- `delivery.mode` is `autonomous` (the default when the key is missing, decision D3). `human-gated` refuses: a
  human merges. Any other value refuses as invalid.
- The PR is open, not a draft, and its base is the configured `baseBranch` (`auto` or missing: the repository's
  default branch).
- GitHub reports it MERGEABLE and CLEAN, no review decision requests changes, and the head is not behind the base
  (the GitHub comparison of base and head, whatever the branch protection says).
- It carries none of the labels `qa-failed`, `do-not-merge`, `blocked`, `qa` (a tester is on it) and
  `in-progress` (a run holds it).
- An independent review record is on the current head: a PR review from an OWNER, MEMBER or COLLABORATOR whose
  commit is the head and whose body has the lines `Independent review: APPROVE`, `Head: <head>` and
  `Reviewer session: <id>`. Reviews are ordered by `submittedAt`, not by their position in the API list; a trusted,
  non-PENDING review without a `YYYY-MM-DDTHH:MM:SSZ` time makes the PR unreadable (exit 2). An
  approval counts only in the GitHub state COMMENTED (the record posted from the
  project's one account) or APPROVED. Other authors' reviews and DISMISSED and PENDING reviews are ignored. The
  latest record on the head decides: `Independent review: CHANGES_REQUESTED` refuses, and so does a trusted
  CHANGES_REQUESTED-state review on the head, with or without the record line, until a later approval record
  supersedes it. Independence is the session check: with `--author-session`, a record from that session refuses, so a
  second GitHub account is optional. A record on another head does not count. `--merge` always checks this: without a non-empty `--author-session` it refuses
  (`author_session_missing`) and never merges.
- The PR has required checks, and every one passed (or was skipped) on the head. No required checks refuses.
- Unless `qaGate` is false: `qa_freshness.py check` passes on the head for both iOS and Android, from the verdict
  records in PR comments by an OWNER, MEMBER or COLLABORATOR. A stale, unverified, failed or missing platform
  refuses; carried rows are proven against the local history with rerun_scope.py. A PR with `skip-qa` and
  without `needs-qa` needs no verdict, but only when every path it changes since its merge base is a test path,
  CI or docs (path classes of qa_contract.py, read at the merge base, so the PR cannot reclassify its own paths);
  an app input or an unclassified path refuses.
- Strict carry mode (`qa.carryMode: "strict"` in the config at the merge base, the switch a project under a
  coordinator sets; `--strict` makes one run strict too and never relaxes it): each carried row needs a carry record
  listing exactly `git diff --no-renames --name-only` between the two heads, and `skip-qa` also refuses CI paths and
  Markdown below the root (the closed list of rerun_scope.py).
- The head did not move while the gate read the PR.

With `--merge`, a passing gate squash-merges exactly that head: `gh pr merge <n> --squash --match-head-commit
<head>`. A refused gate never merges. The caller reads the merge back. Prints one JSON object; exit 0 passed (and
merged with `--merge`), 1 refused or the merge failed, 2 when an input cannot be read."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from qa_contract import CONFIG, ContractError, carry_mode, changed_paths, classify, path_classes
from qa_freshness import records_in, scope_checker, status
from scenarios import CATALOG

MODES = ('autonomous', 'human-gated')
PR_FIELDS = ('number,state,isDraft,baseRefName,headRefOid,mergeable,mergeStateStatus,reviewDecision,labels,reviews,'
             'comments')
RECORD = re.compile(r'^Independent review: (APPROVE|CHANGES_REQUESTED)[ \t]*$', re.M)
HEAD_LINE = re.compile(r'^Head: ([0-9a-f]{40})[ \t]*$', re.M)
SESSION = re.compile(r'^Reviewer session: (\S[^\n]*?)[ \t]*$', re.M)
SHA = re.compile(r'[0-9a-f]{40}')
SUBMITTED = re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ')
PASSED_CHECKS = ('pass', 'skipping')
BLOCKING_LABELS = ('qa-failed', 'do-not-merge', 'blocked', 'qa', 'in-progress')
TRUSTED = ('OWNER', 'MEMBER', 'COLLABORATOR')
RECORD_STATES = ('COMMENTED', 'APPROVED')  # the only states an approval record can have
SHOWN_PATHS = 10


class Unreadable(RuntimeError):
    pass


def gh(project: Path, *args: str, ok_codes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    try:
        done = subprocess.run(['gh', *args], cwd=project, capture_output=True, text=True)
    except OSError as error:
        raise Unreadable(f'gh: {type(error).__name__}') from error
    if done.returncode not in ok_codes:
        raise Unreadable(f'gh {args[0]} {args[1]}: exit {done.returncode}: {first_line(done.stderr)}')
    return done


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), '')


def parse_json(text: str, what: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise Unreadable(f'{what}: not JSON') from error


def read_config(project: Path) -> dict[str, Any]:
    path = project / CONFIG
    try:
        config = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Unreadable(f'{CONFIG}: {type(error).__name__}') from error
    if not isinstance(config, dict):
        raise Unreadable(f'{CONFIG}: not an object')
    return config


def delivery_mode(config: dict[str, Any]) -> str:
    delivery = config.get('delivery', {})
    return delivery.get('mode', 'autonomous') if isinstance(delivery, dict) else 'invalid'


def base_branch(project: Path, config: dict[str, Any]) -> str:
    value = config.get('baseBranch')
    if value in (None, 'auto'):
        done = gh(project, 'repo', 'view', '--json', 'defaultBranchRef', '--jq', '.defaultBranchRef.name')
        value = done.stdout.strip()
    if not isinstance(value, str) or not value:
        raise Unreadable('baseBranch: not a branch name')
    return value


def trusted(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [item for item in items or [] if item.get('authorAssociation') in TRUSTED]


def review_refusals(pr: dict[str, Any], head: str, author_session: str | None) -> list[str]:
    records = []
    # Oldest first by submission time. Every counted review needs a UTC `submittedAt` in GitHub's whole-second form,
    # so the strings sort in time order; a missing or other time is unreadable, never guessed (fail closed). The
    # stable sort keeps the API order only for equal times.
    reviews = [r for r in trusted(pr.get('reviews')) if r.get('state') != 'PENDING']
    for review in reviews:
        when = review.get('submittedAt')
        if not (isinstance(when, str) and SUBMITTED.fullmatch(when)):
            raise Unreadable(f'gh pr view: review submittedAt {json.dumps(when)} is not YYYY-MM-DDTHH:MM:SSZ')
    for review in sorted(reviews, key=lambda r: r['submittedAt']):
        commit = (review.get('commit') or {}).get('oid')
        if review.get('state') == 'CHANGES_REQUESTED':
            # A GitHub "Request changes" review rejects its commit whatever its body says; never an approval.
            records.append({'verdict': 'CHANGES_REQUESTED', 'commit': commit, 'head': commit, 'session': None})
            continue
        if review.get('state') not in RECORD_STATES:
            continue  # DISMISSED and PENDING reviews are ignored
        body = review.get('body') or ''
        verdicts = RECORD.findall(body)
        if not verdicts:
            continue
        lines = HEAD_LINE.findall(body)
        sessions = SESSION.findall(body)
        records.append({'verdict': verdicts[-1], 'commit': commit,
                        'head': lines[-1] if lines else None, 'session': sessions[-1] if sessions else None})
    on_head = [r for r in records if r['commit'] == head and r['head'] == head]
    if not on_head:
        other = sorted({r['head'] or r['commit'] or 'unknown' for r in records})
        return [f'review_not_on_head: {", ".join(other)}'] if other else ['review_missing']
    latest = on_head[-1]
    if latest['verdict'] != 'APPROVE':
        return ['review_changes_requested']
    if not latest['session']:
        return ['reviewer_session_missing']
    if author_session is not None and latest['session'] == author_session:
        return ['reviewer_session_is_author']
    return []


def check_refusals(project: Path, number: str) -> list[str]:
    # gh exits 8 while checks are pending and 1 when one failed or none is required; the JSON still decides.
    done = gh(project, 'pr', 'checks', number, '--required', '--json', 'name,bucket', ok_codes=(0, 1, 8))
    if not done.stdout.strip():
        if 'no required checks' in done.stderr:
            return ['required_checks_missing']
        raise Unreadable(f'gh pr checks: exit {done.returncode}: {first_line(done.stderr)}')
    checks = parse_json(done.stdout, 'gh pr checks')
    if not isinstance(checks, list):
        raise Unreadable('gh pr checks: not a list')
    if not checks:
        return ['required_checks_missing']
    return [f'required_check_{"pending" if c.get("bucket") == "pending" else "not_passed"}: {c.get("name")} '
            f'({c.get("bucket")})' for c in checks if c.get('bucket') not in PASSED_CHECKS]


def compare(project: Path, base: str, head: str) -> tuple[int, str]:
    """(commits the head is behind the base, the merge base SHA), from the GitHub comparison."""
    done = gh(project, 'api', f'repos/{{owner}}/{{repo}}/compare/{quote(base, safe="")}...{head}', '--jq',
              '{behind_by: .behind_by, merge_base: .merge_base_commit.sha}')
    data = parse_json(done.stdout, 'gh api compare')
    behind, merge_base = (data.get('behind_by'), data.get('merge_base')) if isinstance(data, dict) else (None, None)
    if not isinstance(behind, int) or isinstance(behind, bool) or not isinstance(merge_base, str) \
            or not SHA.fullmatch(merge_base):
        raise Unreadable('gh api compare: no behind_by or merge base')
    return behind, merge_base


def skip_qa_refusals(project: Path, merge_base: str, head: str, strict: bool = False) -> list[str]:
    """Why skip-qa does not apply: a changed path that is an app input or in no class (in strict carry mode also a
    CI path, and Markdown below the root). Empty when it applies."""
    try:
        strict = strict or carry_mode(project, merge_base) == 'strict'
        changes = classify(changed_paths(project, merge_base, head), path_classes(project, merge_base, strict), strict)
    except ContractError as error:
        return [f'skip_qa_unverifiable: {error} (fetch the PR head and the base)']
    blocked = changes['app'] + changes['other'] + (changes['ci'] if strict else [])
    if not blocked:
        return []
    more = f' (+{len(blocked) - SHOWN_PATHS} more)' if len(blocked) > SHOWN_PATHS else ''
    return [f'skip_qa_not_allowed: {", ".join(blocked[:SHOWN_PATHS])}{more}']


def qa_base(project: Path, base: str) -> str:
    remote = f'refs/remotes/origin/{base}'
    done = subprocess.run(['git', '-C', str(project), 'rev-parse', '--verify', '-q', remote], capture_output=True)
    return f'origin/{base}' if done.returncode == 0 else base


def qa_refusals(project: Path, pr: dict[str, Any], head: str, base: str,
                strict: bool = False) -> tuple[list[str], dict[str, Any] | None]:
    records = records_in({'comments': trusted(pr.get('comments'))})
    try:
        checker = scope_checker(project, CATALOG, qa_base(project, base), strict)
        result = status(records, head, eligible=checker, carry_paths=checker.paths)
    except ContractError as error:
        return [f'qa_unreadable: {error}'], None
    if result['gate'] == 'pass':
        return [], result
    out = []
    for platform, row in result['platforms'].items():
        if row['status'] != 'fresh':
            out.append(f'qa_{row["status"]}: {platform}' + (f' ({row["reason"]})' if 'reason' in row else ''))
        elif row['verdict'] != 'PASS':
            out.append(f'qa_failed: {platform}')
    return out, result


def evaluate(project: Path, number: str, author_session: str | None, strict: bool = False) -> dict[str, Any]:
    config = read_config(project)
    mode = delivery_mode(config)
    if mode not in MODES:
        return {'pr': number, 'gate': 'refused', 'refusals': ['delivery_mode_invalid']}
    if mode == 'human-gated':
        return {'pr': number, 'gate': 'refused', 'refusals': ['delivery_human_gated: a human merges']}
    pr = parse_json(gh(project, 'pr', 'view', number, '--json', PR_FIELDS).stdout, 'gh pr view')
    if not isinstance(pr, dict):
        raise Unreadable('gh pr view: not an object')
    head = pr.get('headRefOid') or ''
    if not SHA.fullmatch(head):
        raise Unreadable('gh pr view: no head SHA')
    base = base_branch(project, config)
    labels = {label.get('name') for label in pr.get('labels') or []}
    refusals: list[str] = []
    if pr.get('state') != 'OPEN':
        refusals.append(f'pr_not_open: {pr.get("state")}')
    if pr.get('isDraft'):
        refusals.append('pr_draft')
    if pr.get('baseRefName') != base:
        refusals.append(f'base_not_configured: {pr.get("baseRefName")} (baseBranch {base})')
    if pr.get('mergeable') != 'MERGEABLE' or pr.get('mergeStateStatus') != 'CLEAN':
        refusals.append(f'not_mergeable: {pr.get("mergeable")}/{pr.get("mergeStateStatus")}')
    behind, merge_base = compare(project, base, head)
    if behind:
        refusals.append(f'behind_base: {behind} commit(s) on {base}')
    refusals += [f'blocking_label: {label}' for label in BLOCKING_LABELS if label in labels]
    if pr.get('reviewDecision') == 'CHANGES_REQUESTED':
        refusals.append('changes_requested')
    refusals += review_refusals(pr, head, author_session)
    refusals += check_refusals(project, number)
    qa: Any = 'not_required'
    if config.get('qaGate') is not False:
        if 'skip-qa' in labels and 'needs-qa' not in labels:
            problems = skip_qa_refusals(project, merge_base, head, strict)
            refusals += problems
            qa = 'skip_qa_rejected' if problems else 'skip_qa'
        else:
            problems, result = qa_refusals(project, pr, head, base, strict)
            refusals += problems
            qa = result['platforms'] if result else None
    again = parse_json(gh(project, 'pr', 'view', number, '--json', 'headRefOid').stdout, 'gh pr view')
    if not isinstance(again, dict) or again.get('headRefOid') != head:
        refusals.append('head_moved')
    return {'pr': number, 'head': head, 'base': base, 'mergeBase': merge_base,
            'gate': 'refused' if refusals else 'pass', 'refusals': refusals, 'qa': qa}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Refuse a merge unless review, required checks and QA are on the head')
    parser.add_argument('--pr', required=True)
    parser.add_argument('--project', default='.')
    parser.add_argument('--author-session', help='the authoring session; a review record from it refuses (required '
                        'with --merge)')
    parser.add_argument('--merge', action='store_true', help='squash-merge the exact head when the gate passes')
    parser.add_argument('--strict', action='store_true',
                        help='strict carry mode even when qa.carryMode at the merge base is classic')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[1-9][0-9]*', args.pr):
        parser.error('--pr must be a PR number')
    project = Path(args.project)
    author = (args.author_session or '').strip() or None
    try:
        result = evaluate(project, args.pr, author, args.strict)
    except Unreadable as error:
        print(json.dumps({'pr': args.pr, 'gate': 'unreadable', 'code': str(error)}))
        return 2
    if args.merge and author is None:
        # Merging always checks review independence, so it needs the authoring session.
        result['refusals'].append('author_session_missing: --merge needs --author-session')
        result['gate'] = 'refused'
    if result['gate'] == 'pass' and args.merge:
        done = subprocess.run(['gh', 'pr', 'merge', args.pr, '--squash', '--match-head-commit', result['head']],
                              cwd=project, capture_output=True, text=True)
        result['merge'] = 'requested' if done.returncode == 0 else f'failed: {first_line(done.stderr)}'
    print(json.dumps(result, indent=2))
    return 0 if result['gate'] == 'pass' and result.get('merge', 'requested') == 'requested' else 1


if __name__ == '__main__':
    sys.exit(main())
