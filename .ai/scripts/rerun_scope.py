"""Which QA results of a tested head carry over to a new head, and which scenarios run again.

    python3 -B .ai/scripts/rerun_scope.py --tested <sha> --head <sha> --base <ref> [--strict] [--catalog <path>]
        [--repo <root>] [--id <ID>]...

By default a new head needs new evidence. Results carry over only when the app did not change: every path changed
between `--tested` and `--head` is a test path (runner, flows, scripts, tests), CI or docs. App inputs are `lib/`,
`assets/`, `pubspec.*`, `android/`, `ios/`, the FVM pin, `l10n.yaml` and `build.yaml`; test paths `.maestro/`,
`integration_test/`, `test/`, `test_driver/` and `e2e/`; CI `.github/`, `codemagic.yaml`, `.gitlab-ci.yml` and
`bitrise.yml`; docs `docs/` and any other `*.md`. The project config can
replace each list (`qa.rerunPaths` in .ai/agentic.config.json, read at the merge base of `--base` and `--head`, so
neither the tested head nor the new head of a PR can reclassify its own paths). A changed app input, or a path in no
class, reruns everything.

`--base` (the PR's base branch) is required. A head that merged its base is compared by the PR's own patch: a path counts
as changed only when its diff against the merge base differs between the two heads. A file the base did not change
is compared directly (tested against head). For a file the base changed, the comparison keeps every changed and
context byte, whitespace included, and ignores only blob IDs and hunk line numbers. When both heads share the merge
base, the direct diff decides. A base merge that left the app patch identical therefore carries
results over.

Strict carry mode (`qa.carryMode: "strict"` in the config at the merge base, or `--strict`, which can only make it
stricter) is the coordination contract's closed list. Every path of
`git diff --no-renames --name-only <tested>..<head>` counts (a rename is its old and its new path), base-merge paths
included, so a base update that brought app paths reruns everything. A tested head without history shared with the
base is unreadable (`no_merge_base`). Only test paths, process paths
(`.ai/specs/`, `.ai/runs/`, `.ai/skills/`, `.agents/`, `.claude/`), `docs/` and root Markdown carry; CI paths and
Markdown elsewhere rerun everything; a configured `appInputs` list only adds to the defaults. The output's
`changedPaths` is that diff. It never replaces the QA lane's own run of the diff: the lane runs it, checks that it
equals `changedPaths`, and records it in the verdict record's `carry` entry, which qa_freshness.py checks. The same
head returns `same_head` without reading the merge base or the config.

When results carry over, a scenario still runs again when its catalog entry changed or is new, or when its own
Maestro flow or script changed, directly or through a changed file it references by name (a subflow or script,
followed transitively through the flow and script files under the test paths). `--id` (repeatable) limits the
answer to the scenarios the earlier verdict covered; the default is every scenario in the catalog at `--head`.

Carry-over is per platform: a result moves only into the same platform's verdict on the new head
(`"result": "NOT_RUN"` with `carriedFrom`), never into the other platform's. Prints one JSON object with `status`
(`same_head`, `carry_over` or `rerun_all`), the reason, `mode`, `changedPaths`, the classified changes, `rerun` and
`carryOver`; exit 0, or 2 when an input cannot be read."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from qa_contract import (ContractError, carry_mode, changed_paths, classify, files_under, git, merge_base, path_classes,
                         resolve, show)
from scenarios import CATALOG, catalog_errors, load_at

REFERENCING = ('.yaml', '.yml', '.js')
HUNK = re.compile(rb'^@@ -[0-9]+(?:,[0-9]+)? \+[0-9]+(?:,[0-9]+)? @@')


def patch_digest(repo: Path, old: str, new: str, path: str) -> str | None:
    """A digest of path's change from old to new that keeps every byte of the changed and context lines (whitespace
    included) and drops only what moves with the base: the blob IDs (`index` line) and the hunk line numbers. None
    when the path did not change."""
    diff = git(repo, 'diff', '--no-renames', '--no-ext-diff', '--no-textconv', '--no-color', '--binary', old, new, '--',
               ':(literal)' + path).stdout
    if not diff:
        return None
    lines = [HUNK.sub(b'@@', line) for line in diff.split(b'\n') if not line.startswith(b'index ')]
    return hashlib.sha256(b'\n'.join(lines)).hexdigest()


def blob(repo: Path, rev: str, path: str) -> str:
    """The blob ID of path in rev, or '' when rev has no such file."""
    result = git(repo, 'rev-parse', '--verify', '--quiet', f'{rev}:{path}', ok_codes=(0, 1, 128))
    return result.stdout.decode().strip() if result.returncode == 0 else ''


def own_changes(repo: Path, base: str, tested: str, head: str) -> list[str]:
    """Paths whose PR patch (against the merge base with base) differs between tested and head. With the same merge
    base for both heads, that is the direct diff between them. Per path, when the base did not change the file, the
    file itself is compared (tested against head); the line-number-free patch digest decides only for a file the
    base changed, so an edit moved between two identical blocks is still a change."""
    old_base, new_base = merge_base(repo, base, tested), merge_base(repo, base, head)
    if old_base == new_base:
        return changed_paths(repo, tested, head)
    paths = sorted(set(changed_paths(repo, old_base, tested)) | set(changed_paths(repo, new_base, head)))
    out = []
    for path in paths:
        if blob(repo, old_base, path) == blob(repo, new_base, path):
            changed = blob(repo, tested, path) != blob(repo, head, path)
        else:
            changed = patch_digest(repo, old_base, tested, path) != patch_digest(repo, new_base, head, path)
        if changed:
            out.append(path)
    return out


def touched_test_files(repo: Path, head: str, changed: list[str], test_paths: list[str]) -> set[str]:
    """The changed test files plus every flow or script under the test paths that references one by name,
    transitively."""
    touched = set(changed)
    texts = {}
    for prefix in test_paths:
        for path in files_under(repo, head, prefix):
            if path.endswith(REFERENCING):
                texts[path] = (show(repo, head, path) or b'').decode('utf-8', errors='replace')
    grew = True
    while grew:
        names = {p.rsplit('/', 1)[-1] for p in touched}
        pattern = re.compile(r'(?<![\w.-])(' + '|'.join(map(re.escape, sorted(names))) + r')(?![\w.-])') if names else None
        new = {path for path, text in texts.items() if path not in touched and pattern and pattern.search(text)}
        touched |= new
        grew = bool(new)
    return touched


def own_files(scenario: dict[str, Any]) -> list[str]:
    return ([scenario['maestroFlow']] if scenario['maestroFlow'] else []) + scenario.get('scripts', [])


def scope(repo: Path, tested: str, head: str, base: str, catalog_path: str = CATALOG,
          ids: list[str] | None = None, strict: bool = False) -> dict[str, Any]:
    tested, head = resolve(repo, tested), resolve(repo, head)
    catalog = load_at(repo, head, catalog_path)
    if catalog is None:
        raise ContractError(f'{head}:{catalog_path}: catalog_missing')
    errors = catalog_errors(catalog)
    if errors:
        raise ContractError(f'{head}:{catalog_path}: catalog_invalid: ' + '; '.join(errors))
    known = [s['id'] for s in catalog['scenarios']]
    wanted = [i for i in known if ids is None or i in ids]
    out: dict[str, Any] = {'tested': tested, 'head': head, 'base': resolve(repo, base),
                           'unknownIds': [i for i in ids or [] if i not in known]}
    if tested == head:  # as before: the same head reads neither the merge base nor the config
        return {**out, 'status': 'same_head', 'reason': 'the tested head is the head',
                'mode': 'strict' if strict else 'classic', 'changedPaths': [], 'changes': None, 'rerun': [],
                'carryOver': wanted}
    # The mode and the path classes come from the merge base, never from the head: a PR cannot reclassify its own
    # app code or relax the mode. --strict can only make it stricter.
    at = merge_base(repo, out['base'], head)
    strict = strict or carry_mode(repo, at) == 'strict'
    if strict:
        merge_base(repo, out['base'], tested)  # unrelated history is unreadable (no_merge_base), as in classic mode
    raw = changed_paths(repo, tested, head)
    out.update(mode='strict' if strict else 'classic', changedPaths=sorted(raw))
    classes = path_classes(repo, at, strict)
    # Strict: every path of `git diff --no-renames --name-only tested..head` counts, base-merge paths included.
    effective = raw if strict else own_changes(repo, out['base'], tested, head)
    changes = classify(effective, classes, strict)
    out['changes'] = changes
    if changes['app'] or changes['other'] or (strict and changes['ci']):
        reason = ('app_inputs_changed' if changes['app'] else 'unclassified_paths_changed' if changes['other']
                  else 'ci_paths_changed')
        return {**out, 'status': 'rerun_all', 'reason': reason, 'rerun': wanted, 'carryOver': []}
    test_changes = classify(raw, classes)['test']
    touched = touched_test_files(repo, head, test_changes, classes['testPaths'])
    before = load_at(repo, tested, catalog_path)
    earlier = {s['id']: s for s in before['scenarios']} if isinstance(before, dict) and isinstance(
        before.get('scenarios'), list) and all(isinstance(s, dict) and 'id' in s for s in before['scenarios']) else {}
    rerun = []
    for scenario in catalog['scenarios']:
        sid = scenario['id']
        if sid in wanted and (earlier.get(sid) != scenario or any(p in touched for p in own_files(scenario))):
            rerun.append(sid)
    return {**out, 'status': 'carry_over',
            'reason': 'only test, process or doc paths changed' if strict else 'only test paths, CI or docs changed',
            'rerun': rerun, 'carryOver': [i for i in wanted if i not in rerun]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Which QA results carry over from a tested head to a new head')
    parser.add_argument('--tested', required=True, help='the head the earlier QA verdict was recorded on')
    parser.add_argument('--head', required=True, help='the new head')
    parser.add_argument('--base', required=True,
                        help="the PR's base branch: the path classes come from its merge base with --head")
    parser.add_argument('--catalog', default=CATALOG)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--id', action='append', dest='ids', help='a scenario the earlier verdict covered')
    parser.add_argument('--strict', action='store_true',
                        help='strict carry mode even when qa.carryMode at the merge base is classic')
    args = parser.parse_args(argv)
    try:
        result = scope(Path(args.repo), args.tested, args.head, args.base, args.catalog, args.ids, args.strict)
    except ContractError as error:
        print(json.dumps({'status': 'unreadable', 'code': str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
