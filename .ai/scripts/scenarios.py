"""The project's QA scenario catalog: validate it, render tester instructions, list the IDs a diff requires.

    python3 -B .ai/scripts/scenarios.py validate [--catalog <path>] [--project <root>]
    python3 -B .ai/scripts/scenarios.py render [--catalog <path>] [--platform ios|android] [--id <ID>]...
    python3 -B .ai/scripts/scenarios.py required --base <ref> --head <ref> [--catalog <path>] [--repo <root>]

The catalog (default `.maestro/scenarios.json`) follows .ai/schemas/scenarios.schema.json: scenarios with a stable
ID, a feature-ledger ID, a title, platforms, a state (planned, source-implemented, simulator-passed,
device-passed), steps with an expected observation each, cleanup, the Maestro flow path (null while there is none)
and optional other scripts; and feature groups (`name`, `sourcePrefixes`, `requiredScenarioIds`). The same scenario
ID is used in the task, the spec, these instructions, the evidence and the QA verdict.

`validate` checks the schema, unique scenario IDs and group names, that every required ID exists, plain repository
paths, that a scenario past `planned` has a flow or a script, and that every flow and script exists and is not
empty (a Maestro flow needs at least one command after its `---` header, and every entry must be a command: a bare
`-`, a comment-only entry or an empty value is refused). Exit 0 valid, 1 invalid, 2 unreadable.

`render` prints Markdown instructions for a tester: per scenario its steps with the expected observation, and its
cleanup. `--platform` keeps the scenarios of one platform; `--id` (repeatable) keeps the named ones, for example
the IDs `required` printed.

`required` reads the catalog at `--head` and the paths changed by `--head` since its merge base with `--base`; the
path classes come from that merge base, so a PR cannot reclassify its own app code (in strict carry mode a
configured `appInputs` list only adds to the defaults).
A changed path under a group's `sourcePrefixes` names that group and adds its `requiredScenarioIds`; a changed flow
or script of a scenario adds that scenario. The group's IDs enter the QA run by reference: a spec names the group,
not a copy of its IDs. Changed app inputs (see rerun_scope.py) that no group covers are listed as `uncovered`.
Prints one JSON object; exit 0, or 1 when the catalog at head is invalid, 2 when it cannot be read."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

from qa_contract import (ContractError, carry_mode, changed_paths, load_schema, merge_base, path_classes,
                         read_json_file, repo_path_error, resolve, schema_errors, show, under)

CATALOG = '.maestro/scenarios.json'
PLATFORMS = ('ios', 'android')
# A Maestro command is a top-level sequence item: `- launchApp`, `- tapOn: ...`.
ENTRY = re.compile(r'-(\s|$)')
COMMENT = re.compile(r'(^|\s)#.*$')
EMPTY_VALUES = {'{}', '[]', 'null', 'Null', 'NULL', '~', '!!null', '""', "''"}  # compared without whitespace
Reader = Callable[[str], 'bytes | None']


def flow_problem(data: bytes) -> str | None:
    """Why a Maestro flow runs nothing, or None. Every top-level entry after the `---` header must be a command: a
    bare `-` with nothing indented below it, a comment-only entry and an empty value (`{}`, `[ ]`, `null`, `~`,
    `!!null`, `""`; whitespace ignored) are refused, and so is a flow with no entry."""
    try:
        lines = data.decode('utf-8').splitlines()
    except UnicodeDecodeError:
        return 'empty_flow'
    lines = [line for line in (COMMENT.sub('', line).rstrip() for line in lines) if line.strip()]
    if '---' in lines:
        lines = lines[lines.index('---') + 1:]
    entries: list[tuple[str, list[str]]] = []
    for line in lines:
        if ENTRY.match(line):
            entries.append((line[1:].strip(), []))
        elif line[0].isspace() and entries:
            entries[-1][1].append(line)
    if not entries:
        return 'empty_flow'
    for number, (value, below) in enumerate(entries, 1):
        if (re.sub(r'\s+', '', value) in EMPTY_VALUES) if value else not below:
            return f'empty_command entry {number}'
    return None


def catalog_errors(catalog: Any, read: Reader | None = None) -> list[str]:
    """Every problem of the catalog; with read (repository path -> bytes or None), also of its flow and script
    files."""
    errors = [f'schema: {e}' for e in schema_errors(catalog, load_schema('scenarios.schema.json'))]
    if errors:
        return errors
    scenarios = catalog['scenarios']
    ids = [s['id'] for s in scenarios]
    errors += [f'duplicate_scenario_id: {i}' for i in sorted({i for i in ids if ids.count(i) > 1})]
    names = [g['name'] for g in catalog['featureGroups']]
    errors += [f'duplicate_group: {n}' for n in sorted({n for n in names if names.count(n) > 1})]
    for group in catalog['featureGroups']:
        errors += [f'unknown_required_id: {group["name"]}: {i}' for i in group['requiredScenarioIds'] if i not in ids]
        errors += [f'bad_path: {group["name"]}: {p}: {why}' for p in group['sourcePrefixes']
                   if (why := repo_path_error(p))]
    for scenario in scenarios:
        sid, flow, scripts = scenario['id'], scenario['maestroFlow'], scenario.get('scripts', [])
        if scenario['state'] != 'planned' and flow is None and not scripts:
            errors.append(f'no_flow: {sid}: state {scenario["state"]} needs a Maestro flow or a script')
        for path in ([flow] if flow else []) + scripts:
            if why := repo_path_error(path):
                errors.append(f'bad_path: {sid}: {path}: {why}')
                continue
            if read is None:
                continue
            data = read(path)
            if data is None:
                errors.append(f'missing_file: {sid}: {path}')
            elif path == flow and (problem := flow_problem(data)):
                code, _, detail = problem.partition(' ')
                errors.append(f'{code}: {sid}: {path}' + (f' ({detail})' if detail else ''))
            elif not data.strip():
                errors.append(f'empty_flow: {sid}: {path}')
    return errors


def worktree_reader(root: Path) -> Reader:
    def read(path: str) -> bytes | None:
        target = root / path
        return target.read_bytes() if target.is_file() else None
    return read


def load_at(repo: Path, rev: str, path: str) -> Any:
    """The catalog at rev, parsed, or None when rev has no catalog."""
    data = show(repo, rev, path)
    if data is None:
        return None
    try:
        return json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f'{rev}:{path}: {type(error).__name__}') from error


def render(catalog: dict[str, Any], platform: str | None = None, ids: list[str] | None = None) -> str:
    """Markdown tester instructions for the selected scenarios, in catalog order."""
    chosen = [s for s in catalog['scenarios'] if (platform is None or platform in s['platforms'])
              and (not ids or s['id'] in ids)]
    title = 'QA scenarios' + (f' ({platform})' if platform else '')
    out = [f'# {title}', '']
    if not chosen:
        out += ['No scenario matches.', '']
    for scenario in chosen:
        out += [f'## {scenario["id"]}: {scenario["title"]}', '',
                f'- Feature: {scenario["feature"]}',
                f'- Platforms: {", ".join(scenario["platforms"])}',
                f'- State: {scenario["state"]}',
                f'- Maestro flow: {scenario["maestroFlow"] or "none yet"}']
        if scenario.get('scripts'):
            out.append(f'- Scripts: {", ".join(scenario["scripts"])}')
        out += ['', 'Steps:', '']
        out += [f'{n}. {step["action"]}\n   Expect: {step["expect"]}' for n, step in enumerate(scenario['steps'], 1)]
        out += ['', 'Cleanup:', '']
        out += [f'- {item}' for item in scenario['cleanup']] or ['- Nothing to clean up.']
        out.append('')
    return '\n'.join(out)


def required(catalog: dict[str, Any], paths: list[str], app_inputs: list[str]) -> dict[str, Any]:
    """The groups and scenario IDs the changed paths require."""
    reasons: dict[str, list[str]] = {}
    groups = []
    for group in catalog['featureGroups']:
        hit = [p for p in paths if under(p, group['sourcePrefixes'])]
        if hit:
            groups.append({'name': group['name'], 'paths': hit, 'requiredScenarioIds': group['requiredScenarioIds']})
            for sid in group['requiredScenarioIds']:
                reasons.setdefault(sid, []).append('group:' + group['name'])
    for scenario in catalog['scenarios']:
        own = ([scenario['maestroFlow']] if scenario['maestroFlow'] else []) + scenario.get('scripts', [])
        if any(p in paths for p in own):
            reasons.setdefault(scenario['id'], []).append('flow_changed')
    covered = [p for g in catalog['featureGroups'] for p in paths if under(p, g['sourcePrefixes'])]
    return {
        'groups': groups,
        'scenarios': [{'id': s['id'], 'platforms': s['platforms'], 'because': reasons[s['id']]}
                      for s in catalog['scenarios'] if s['id'] in reasons],
        'requiredScenarioIds': [s['id'] for s in catalog['scenarios'] if s['id'] in reasons],
        'uncovered': [p for p in paths if under(p, app_inputs) and p not in covered],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate, render or query the QA scenario catalog')
    commands = parser.add_subparsers(dest='command', required=True)
    validate = commands.add_parser('validate')
    validate.add_argument('--catalog', default=CATALOG)
    validate.add_argument('--project', default='.')
    draw = commands.add_parser('render')
    draw.add_argument('--catalog', default=CATALOG)
    draw.add_argument('--project', default='.')
    draw.add_argument('--platform', choices=PLATFORMS)
    draw.add_argument('--id', action='append', dest='ids')
    query = commands.add_parser('required')
    query.add_argument('--base', required=True)
    query.add_argument('--head', required=True)
    query.add_argument('--catalog', default=CATALOG)
    query.add_argument('--repo', default='.')
    args = parser.parse_args(argv)
    try:
        if args.command == 'required':
            repo = Path(args.repo)
            head = resolve(repo, args.head)
            catalog = load_at(repo, head, args.catalog)
            if catalog is None:
                raise ContractError(f'{head}:{args.catalog}: catalog_missing')
            errors = catalog_errors(catalog)
            if errors:
                print(json.dumps({'status': 'invalid', 'errors': errors}, indent=2))
                return 1
            base = resolve(repo, args.base)
            paths = changed_paths(repo, base, head, merge_base=True)
            # Path classes from the merge base, never from the head (a PR cannot reclassify its own app code).
            at = merge_base(repo, base, head)
            classes = path_classes(repo, at, carry_mode(repo, at) == 'strict')
            result = required(catalog, paths, classes['appInputs'])
            print(json.dumps({'status': 'ok', 'base': base, 'head': head, **result}, indent=2))
            return 0
        root = Path(args.project)
        catalog = read_json_file(root / args.catalog)
        errors = catalog_errors(catalog, worktree_reader(root))
        if args.command == 'validate' or errors:
            status = 'invalid' if errors else 'valid'
            print(json.dumps({'status': status, 'errors': errors,
                              'scenarios': len(catalog['scenarios']) if not errors else None}, indent=2))
            return 1 if errors else 0
        unknown = [i for i in args.ids or [] if i not in {s['id'] for s in catalog['scenarios']}]
        if unknown:
            print(json.dumps({'status': 'invalid', 'errors': [f'unknown_id: {i}' for i in unknown]}, indent=2))
            return 1
        print(render(catalog, args.platform, args.ids), end='')
        return 0
    except ContractError as error:
        print(json.dumps({'status': 'unreadable', 'code': str(error)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
