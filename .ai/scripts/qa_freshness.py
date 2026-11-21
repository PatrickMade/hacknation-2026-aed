"""QA verdict records: validate one and render its PR comment, or decide freshness and the PR label.

    python3 -B .ai/scripts/qa_freshness.py comment <record.json> [--catalog <path>]
    python3 -B .ai/scripts/qa_freshness.py check --head <current head sha> [--repo <root> --base <ref> [--strict]
        [--repo-catalog <path>]] [--platform ios|android]... [--catalog <path>] <records>...

A record (.ai/schemas/qa-verdict.schema.json) is one platform's verdict pinned to the tested head SHA, with the
installed artifact's app ID, version, build and SHA-256, the recording lane, and one row per scenario ID: PASS
(with its evidence), FAIL (with a reason; `knownIssue` makes a tracked failure an exception) or NOT_RUN (with a
reason; `carriedFrom` names the earlier head whose result on this platform carries over, see rerun_scope.py).
The verdict is PASS only when every row passes, carries over (proven by `check`) or is a known issue; the record's `verdict` must say
so. With `--catalog`, every row's ID must be a catalog scenario for the record's platform.

`comment` validates the record and prints the PR comment: `QA verdict: <platform> <verdict>` and
`QA head: <sha>` lines, the artifact, a row table and the record as a fenced `json` block.

`check` reads records in the order they were recorded. A file holds one record, a JSON list of records, a
`gh ... --json comments` export, or text (such as comment bodies) with fenced `json` record blocks. iOS and Android
each get a status from their latest record:

- `fresh`: the latest record is valid, on the current head, and every carried row is proven;
- `stale`: the latest record is valid but on another head;
- `unverified`: no record, an invalid record (a missing or malformed SHA included), an unclear order (a record on
  the current head followed by one on another head), or a carried row that is not proven. An invalid record with no
  readable platform makes both platforms unverified.

A carried row (`NOT_RUN` with `carriedFrom`) is proven only when an earlier valid record of the same platform on
the `carriedFrom` head passed that scenario (directly or through its own proven carry) and rerun_scope.py, run on
`--repo` (with the required `--base` and `--repo-catalog`), carries that scenario between the two heads. Without
`--repo` no carried row is proven. In strict carry mode (`qa.carryMode: "strict"` at the merge base, or `--strict`)
the record that carries a row also needs a `carry` entry `{from, to, paths}` from that head to its own head, whose
`paths` equal `git diff --no-renames --name-only <from>..<to>` (rerun_scope.py's `changedPaths`); the QA lane runs that diff
itself, so a carry never rests on the owner's word. A record's `carry` entries must name its own head as `to`, an
earlier head as `from`, sorted paths and each `from` once.

One platform's PASS never covers the other. The PR label needs both platforms fresh on the current head:
`qa-approved` when both pass, else `qa-failed`; until then `label` is null and nobody labels the PR. `--platform`
only limits the platforms printed. Under a coordinator the QA lane that records the second platform verdict sets
the label; solo work sets it through self-QA. Prints one JSON object; exit 0 when both platforms are fresh and
passed, 1 otherwise, 2 when an input cannot be read."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

from qa_contract import ContractError, load_schema, read_json_file, schema_errors
from rerun_scope import scope
from scenarios import CATALOG, catalog_errors

PLATFORMS = ('ios', 'android')
KIND = 'qa-verdict'
BLOCK = re.compile(r'^```json[ \t]*\n(.*?)^```[ \t]*$', re.M | re.S)


def computed_verdict(record: dict[str, Any]) -> str:
    def counts(row: dict[str, Any]) -> bool:
        return (row['result'] == 'PASS' or (row['result'] == 'NOT_RUN' and 'carriedFrom' in row)
                or (row['result'] == 'FAIL' and 'knownIssue' in row))
    return 'PASS' if all(counts(row) for row in record['scenarios']) else 'FAIL'


def record_errors(record: Any, catalog: dict[str, Any] | None = None) -> list[str]:
    errors = schema_errors(record, load_schema('qa-verdict.schema.json'))
    if errors:
        return errors
    ids = [row['id'] for row in record['scenarios']]
    errors += [f'duplicate_scenario: {i}' for i in sorted({i for i in ids if ids.count(i) > 1})]
    for row in record['scenarios']:
        sid, result = row['id'], row['result']
        allowed = {'PASS': {'evidence', 'reason'}, 'FAIL': {'evidence', 'reason', 'knownIssue'},
                   'NOT_RUN': {'evidence', 'reason', 'carriedFrom'}}[result]
        errors += [f'{sid}: {key} is not allowed on {result}' for key in sorted(set(row) - {'id', 'result'} - allowed)]
        if result == 'PASS' and 'evidence' not in row:
            errors.append(f'{sid}: PASS needs evidence')
        if result != 'PASS' and 'reason' not in row:
            errors.append(f'{sid}: {result} needs a reason')
        if row.get('carriedFrom') == record['head']:
            errors.append(f'{sid}: carriedFrom must be an earlier head')
    for entry in record.get('carry', []):
        if entry['to'] != record['head']:
            errors.append(f'carry from {entry["from"]}: to must be the record head')
        if entry['from'] == record['head']:
            errors.append('carry: from must be an earlier head')
        if entry['paths'] != sorted(entry['paths']):
            errors.append(f'carry from {entry["from"]}: paths must be sorted')
    sources = [entry['from'] for entry in record.get('carry', [])]
    errors += [f'carry: duplicate from {s}' for s in sorted({s for s in sources if sources.count(s) > 1})]
    if catalog is not None:
        scenarios = {s['id']: s for s in catalog['scenarios']}
        for sid in ids:
            if sid not in scenarios:
                errors.append(f'{sid}: not in the catalog')
            elif record['platform'] not in scenarios[sid]['platforms']:
                errors.append(f'{sid}: not a {record["platform"]} scenario')
    if '```' in json.dumps(record):
        errors.append('no text may contain ``` (it would end the comment\'s json block)')
    if not errors and record['verdict'] != computed_verdict(record):
        errors.append(f'verdict must be {computed_verdict(record)}')
    return errors


def cell(text: str) -> str:
    return text.replace('|', '\\|').replace('\n', ' ')


def comment(record: dict[str, Any]) -> str:
    artifact = record['artifact']
    lines = [f'QA verdict: {record["platform"]} {record["verdict"]}', f'QA head: {record["head"]}',
             f'Artifact: {artifact["appId"]} {artifact["version"]} ({artifact["build"]}), SHA-256 {artifact["sha256"]}',
             f'Recorded by: {record["recordedBy"]}', '', '| Scenario | Result | Details |', '|---|---|---|']
    for row in record['scenarios']:
        details = []
        if 'knownIssue' in row:
            details.append(f'known issue {row["knownIssue"]}')
        if 'carriedFrom' in row:
            details.append(f'carried over from {row["carriedFrom"]}')
        details += [row[key] for key in ('reason', 'evidence') if key in row]
        lines.append(f'| {row["id"]} | {row["result"]} | {cell("; ".join(details))} |')
    return '\n'.join(lines + ['', '```json', json.dumps(record, indent=2), '```', ''])


def records_in(value: Any) -> list[Any]:
    """Records, in order, from parsed JSON: a record, a list, a `{"comments": [...]}` export or comment objects."""
    if isinstance(value, dict) and isinstance(value.get('comments'), list):
        value = value['comments']
    items = value if isinstance(value, list) else [value]
    out: list[Any] = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get('body'), str) and 'kind' not in item:
            out += records_in_text(item['body'])
        else:
            out.append(item)
    return out


def records_in_text(text: str) -> list[Any]:
    """Records from fenced json blocks; a block that names the record kind but is not JSON stays as its text."""
    out: list[Any] = []
    for block in BLOCK.findall(text):
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            if f'"{KIND}"' in block:
                out.append(block)
            continue
        if isinstance(value, dict) and value.get('kind') == KIND:
            out.append(value)
    return out


def read_records(path: Path) -> list[Any]:
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise ContractError(f'{path}: {type(error).__name__}') from error
    try:
        return records_in(json.loads(text))
    except json.JSONDecodeError:
        return records_in_text(text)


Eligible = Callable[[str, str], 'set[str]']
CarryPaths = Callable[[str, str], 'list[str] | None']


def carry_problems(platform: str, index: int, record: dict[str, Any], valid: list[tuple[int, dict[str, Any]]],
                   eligible: Eligible | None, carry_paths: CarryPaths | None = None) -> list[str]:
    """Why the carried rows of record (the index-th input) are not proven, empty when every one is.

    A carried row is proven when a valid record of the same platform, recorded before it, on its `carriedFrom` head
    has a PASS row for the scenario (or a carried row proven the same way), and rerun_scope.py lets that scenario
    carry from that head to this one (`eligible(from, to)` returns the carry-over IDs). In strict carry mode
    (`carry_paths(from, to)` returns the changed paths, None in classic mode) the record that carries the row also
    needs a `carry` entry from that head to its own head whose paths equal that diff."""
    problems: list[str] = []

    def recorded(owner: dict[str, Any], source: str, target: str) -> str | None:
        expected = carry_paths(source, target) if carry_paths else None
        if expected is None:
            return None
        entry = next((e for e in owner.get('carry', []) if e['from'] == source and e['to'] == target), None)
        if entry is None:
            return f'no carry record from {source}'
        if entry['paths'] != expected:
            return f'the carry record from {source} does not list the paths of git diff --no-renames --name-only'
        return None

    def proven(sid: str, source: str, target: str, before: int, depth: int, owner: dict[str, Any]) -> str | None:
        earlier = [(i, r) for i, r in valid if i < before and r['platform'] == platform and r['head'] == source]
        if not earlier:
            return f'no earlier {platform} record on {source}'
        at, prior = earlier[-1]
        row = next((r for r in prior['scenarios'] if r['id'] == sid), None)
        if row is None:
            return f'the {platform} record on {source} has no row'
        if eligible is None:
            return 'carry-over not checked (no --repo)'
        if sid not in eligible(source, target):
            return f'rerun_scope does not carry it from {source}'
        if why := recorded(owner, source, target):
            return why
        if row['result'] == 'PASS':
            return None
        if row['result'] == 'NOT_RUN' and 'carriedFrom' in row and depth < len(valid):
            return proven(sid, row['carriedFrom'], source, at, depth + 1, prior)
        return f'the {platform} result on {source} is {row["result"]}'

    for row in record['scenarios']:
        if row['result'] == 'NOT_RUN' and 'carriedFrom' in row:
            why = proven(row['id'], row['carriedFrom'], record['head'], index, 0, record)
            if why:
                problems.append(f'{row["id"]}: {why}')
    return problems


def status(records: list[Any], head: str, show: list[str] | None = None, catalog: dict[str, Any] | None = None,
           eligible: Eligible | None = None, carry_paths: CarryPaths | None = None) -> dict[str, Any]:
    """Freshness of both platforms on head and the PR label. The label and the gate always need an iOS and an Android
    verdict on head; `show` only limits the platforms printed."""
    entries: list[tuple[str | None, dict[str, Any] | None, list[str]]] = []
    for record in records:
        errors = record_errors(record, catalog)
        platform = record.get('platform') if isinstance(record, dict) else None
        entries.append((platform if platform in PLATFORMS else None, None if errors else record, errors))
    valid = [(i, record) for i, (_, record, _) in enumerate(entries) if record is not None]
    unplaced = [errors for platform, _, errors in entries if platform is None]
    result: dict[str, Any] = {}
    for platform in PLATFORMS:
        mine = [(i, record, errors) for i, (p, record, errors) in enumerate(entries) if p == platform]
        if unplaced:
            result[platform] = {'status': 'unverified', 'reason': 'record_without_platform', 'errors': unplaced[-1]}
        elif not mine:
            result[platform] = {'status': 'unverified', 'reason': 'no_record'}
        elif mine[-1][1] is None:
            result[platform] = {'status': 'unverified', 'reason': 'invalid_record', 'errors': mine[-1][2]}
        else:
            index, latest = mine[-1][0], mine[-1][1]
            assert latest is not None
            row = {'verdict': latest['verdict'], 'head': latest['head'], 'recordedBy': latest['recordedBy'],
                   'artifactSha256': latest['artifact']['sha256']}
            if latest['head'] != head:
                unclear = any(record is not None and record['head'] == head for _, record, _ in mine)
                result[platform] = ({'status': 'unverified', 'reason': 'order_unclear', **row} if unclear
                                    else {'status': 'stale', **row})
            elif problems := carry_problems(platform, index, latest, valid, eligible, carry_paths):
                result[platform] = {'status': 'unverified', 'reason': 'carry_over_unproven', 'errors': problems, **row}
            else:
                result[platform] = {'status': 'fresh', **row}
    fresh = all(result[p]['status'] == 'fresh' for p in PLATFORMS)
    passed = fresh and all(result[p]['verdict'] == 'PASS' for p in PLATFORMS)
    label = ('qa-approved' if passed else 'qa-failed') if fresh else None
    shown = {p: result[p] for p in (show or PLATFORMS)}
    return {'head': head, 'platforms': shown, 'label': label, 'gate': 'pass' if passed else 'blocked'}


class ScopeChecker:
    """checker(from, to): the scenario IDs rerun_scope.py carries over from one head to the other;
    checker.paths(from, to): in strict carry mode the paths of `git diff --no-renames --name-only from..to`, else None."""

    def __init__(self, repo: Path, catalog_path: str, base: str, strict: bool = False):
        self.repo, self.catalog_path, self.base, self.strict = repo, catalog_path, base, strict
        self.cache: dict[tuple[str, str], dict[str, Any]] = {}

    def answer(self, source: str, target: str) -> dict[str, Any]:
        if (source, target) not in self.cache:
            self.cache[source, target] = scope(self.repo, source, target, self.base, self.catalog_path,
                                               strict=self.strict)
        return self.cache[source, target]

    def __call__(self, source: str, target: str) -> set[str]:
        answer = self.answer(source, target)
        return set(answer['carryOver']) if answer['status'] in ('carry_over', 'same_head') else set()

    def paths(self, source: str, target: str) -> list[str] | None:
        answer = self.answer(source, target)
        return answer['changedPaths'] if answer['mode'] == 'strict' else None


def scope_checker(repo: Path, catalog_path: str, base: str, strict: bool = False) -> ScopeChecker:
    return ScopeChecker(repo, catalog_path, base, strict)


def load_catalog(path: str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    catalog = read_json_file(Path(path))
    errors = catalog_errors(catalog)
    if errors:
        raise ContractError(f'{path}: catalog_invalid: ' + '; '.join(errors))
    return catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate QA verdict records, render their comment, check freshness')
    commands = parser.add_subparsers(dest='command', required=True)
    render = commands.add_parser('comment')
    render.add_argument('record')
    render.add_argument('--catalog')
    check = commands.add_parser('check')
    check.add_argument('--head', required=True)
    check.add_argument('--platform', action='append', choices=PLATFORMS, dest='platforms',
                       help='print only this platform; the label and the gate still need both')
    check.add_argument('--catalog', help='catalog file whose scenario IDs every row must use')
    check.add_argument('--repo', help='the app repository, to check carried rows with rerun_scope.py')
    check.add_argument('--base', help="the PR's base branch, passed to rerun_scope.py (required with --repo)")
    check.add_argument('--strict', action='store_true',
                       help='strict carry mode even when qa.carryMode at the merge base is classic (needs --repo)')
    check.add_argument('--repo-catalog', default=CATALOG, help='catalog path inside the repository, for rerun_scope.py')
    check.add_argument('records', nargs='+')
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        if args.command == 'comment':
            record = read_json_file(Path(args.record))
            errors = record_errors(record, catalog)
            if errors:
                print(json.dumps({'status': 'invalid', 'errors': errors}, indent=2))
                return 1
            print(comment(record), end='')
            return 0
        if not re.fullmatch(r'[0-9a-f]{40}', args.head):
            parser.error('--head must be a full 40-character lower-case commit SHA')
        if args.strict and not args.repo:
            parser.error('--strict needs --repo: the carry records are checked against the repository history')
        if args.repo and not args.base:
            parser.error('--repo needs --base: rerun_scope.py reads the path classes at the merge base with the base')
        records = [record for path in args.records for record in read_records(Path(path))]
        show: list[str] = list(dict.fromkeys(args.platforms or PLATFORMS))
        checker = scope_checker(Path(args.repo), args.repo_catalog, args.base, args.strict) if args.repo else None
        eligible, carry_paths = (checker, checker.paths) if checker else (None, None)
        result = status(records, args.head, show, catalog, eligible, carry_paths)
    except ContractError as error:
        print(json.dumps({'status': 'unreadable', 'code': str(error)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['gate'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
