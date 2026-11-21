"""Shared parts of the QA contract tools (scenarios.py, qa_freshness.py, rerun_scope.py, qa_evidence.py).

The schemas live in ../schemas next to this directory: core/schemas in the harness, .ai/schemas in a project.
`schema_errors()` checks a value against the subset of JSON Schema those files use (type, const, enum, pattern,
minLength, minItems, uniqueItems, required, properties, additionalProperties: false, items and local $ref), so no
third-party package is needed. Git is read with plain `git` commands; nothing here writes."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

CONFIG = '.ai/agentic.config.json'
# Path classes for rerun scope, skip-qa and uncovered app inputs (prefix match). A project overrides any of the lists
# in its config: {"qa": {"rerunPaths": {"appInputs": [...], "testPaths": [...], "ciPaths": [...],
# "processPaths": [...], "docPaths": [...]}}}. CI paths are not app inputs: a CI-only change needs no device QA.
#
# Two carry modes (`qa.carryMode`, read at the merge base; a caller may only make it stricter with --strict):
# - classic (the default): any `*.md` outside the app inputs counts as docs, CI paths carry, process paths are not a
#   class, and the configured lists replace the defaults.
# - strict (the coordination contract's closed list): only test, process and doc paths and root Markdown carry; CI
#   paths and any other path rerun everything; a configured `appInputs` list only adds to the defaults.
PATH_CLASSES: dict[str, list[str]] = {
    'appInputs': ['lib/', 'assets/', 'pubspec.', 'android/', 'ios/', '.fvm', 'l10n.yaml', 'build.yaml'],
    'testPaths': ['.maestro/', 'integration_test/', 'test/', 'test_driver/', 'e2e/'],
    'ciPaths': ['.github/', 'codemagic.yaml', '.gitlab-ci.yml', 'bitrise.yml'],
    'processPaths': ['.ai/specs/', '.ai/runs/', '.ai/skills/', '.agents/', '.claude/'],
    'docPaths': ['docs/'],
}
CARRY_MODES = ('classic', 'strict')
SCHEMAS = Path(__file__).resolve().parent.parent / 'schemas'
SHA = re.compile(r'[0-9a-f]{40}')
TYPES: dict[str, tuple[type, ...]] = {'object': (dict,), 'array': (list,), 'string': (str,), 'boolean': (bool,),
                                      'integer': (int,), 'null': (type(None),)}


class ContractError(RuntimeError):
    """An input the tools cannot read: a missing file, bad JSON, a failed git command. Exit 2."""


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / name).read_text(encoding='utf-8'))


def _is_type(value: Any, name: str) -> bool:
    if name in ('integer', 'number') and isinstance(value, bool):
        return False
    if name == 'number':
        return isinstance(value, (int, float))
    return isinstance(value, TYPES[name])


def schema_errors(value: Any, schema: dict[str, Any], root: dict[str, Any] | None = None, where: str = '$') -> list[str]:
    """`<JSON path>: <rule>` for every rule of the schema subset that value breaks."""
    root = root or schema
    if '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/$defs/'):
            raise ValueError(f'unsupported $ref {ref}')
        target = root['$defs'][ref[len('#/$defs/'):]]
        return schema_errors(value, {**target, **{k: v for k, v in schema.items() if k not in ('$ref', 'description')}},
                             root, where)
    errors: list[str] = []
    if 'const' in schema and value != schema['const']:
        return [f'{where}: must be {json.dumps(schema["const"])}']
    if 'enum' in schema and value not in schema['enum']:
        return [f'{where}: must be one of {", ".join(json.dumps(v) for v in schema["enum"])}']
    types = schema.get('type')
    if types is not None:
        names = types if isinstance(types, list) else [types]
        if not any(_is_type(value, name) for name in names):
            return [f'{where}: must be {" or ".join(names)}']
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            errors.append(f'{where}: must not be empty')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            errors.append(f'{where}: must match {schema["pattern"]}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            errors.append(f'{where}: needs at least {schema["minItems"]} item(s)')
        if schema.get('uniqueItems') and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(f'{where}: items must be unique')
        if 'items' in schema:
            for index, item in enumerate(value):
                errors += schema_errors(item, schema['items'], root, f'{where}[{index}]')
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{where}: {key} is required')
        properties = schema.get('properties', {})
        for key, item in value.items():
            if key in properties:
                errors += schema_errors(item, properties[key], root, f'{where}.{key}')
            elif schema.get('additionalProperties') is False:
                errors.append(f'{where}: unknown key {key}')
    return errors


def repo_path_error(path: str) -> str | None:
    """Why path is not a plain path relative to the repository root, or None."""
    if path != path.strip() or '\\' in path or path.startswith(('/', './')):
        return 'not a plain repository path'
    if any(part == '..' for part in path.split('/')):
        return 'leaves the repository'
    return None


def read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f'{path}: {type(error).__name__}') from error


def git(repo: Path, *args: str, ok_codes: tuple[int, ...] = (0,), stdin: bytes | None = None
        ) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, input=stdin)
    if result.returncode not in ok_codes:
        raise ContractError(f'git {args[0]} failed: {result.stderr.decode(errors="replace").strip()}')
    return result


def resolve(repo: Path, ref: str) -> str:
    """The full commit SHA of ref."""
    result = git(repo, 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}', ok_codes=(0, 1, 128))
    if result.returncode:
        raise ContractError(f'unknown_revision: {ref}')
    return result.stdout.decode().strip()


def merge_base(repo: Path, one: str, two: str) -> str:
    """The merge base of two commits; none (unrelated histories) is unreadable."""
    result = git(repo, 'merge-base', one, two, ok_codes=(0, 1))
    if result.returncode:
        raise ContractError(f'no_merge_base: {one} and {two} share no history')
    return result.stdout.decode().strip()


def changed_paths(repo: Path, old: str, new: str, merge_base: bool = False) -> list[str]:
    """Paths that differ between two commits (renames as delete plus add). With merge_base, the change new made
    since its merge base with old (`old...new`)."""
    spec = f'{old}...{new}' if merge_base else f'{old}..{new}'
    out = git(repo, 'diff', '--name-only', '--no-renames', '-z', spec).stdout.decode()
    return [path for path in out.split('\0') if path]


def show(repo: Path, rev: str, path: str) -> bytes | None:
    """The file at path in rev, or None when rev has no such file."""
    result = git(repo, 'cat-file', '-e', f'{rev}:{path}', ok_codes=(0, 1, 128))
    if result.returncode:
        return None
    return git(repo, 'show', f'{rev}:{path}').stdout


def files_under(repo: Path, rev: str, prefix: str) -> list[str]:
    """Files under prefix in rev."""
    out = git(repo, 'ls-tree', '-r', '-z', '--name-only', rev, '--', prefix).stdout.decode()
    return [path for path in out.split('\0') if path]


def under(path: str, prefixes: list[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def qa_config(repo: Path, rev: str) -> dict[str, Any]:
    """The `qa` object of the project config at rev ({} without one)."""
    data = show(repo, rev, CONFIG)
    if data is None:
        return {}
    try:
        config = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f'{rev}:{CONFIG}: {type(error).__name__}') from error
    qa = config.get('qa') if isinstance(config, dict) else None
    return qa if isinstance(qa, dict) else {}


def carry_mode(repo: Path, rev: str) -> str:
    """`qa.carryMode` of the project config at rev: classic (the default) or strict."""
    mode = qa_config(repo, rev).get('carryMode', 'classic')
    if mode not in CARRY_MODES:
        raise ContractError(f'{rev}:{CONFIG}: qa.carryMode must be one of {", ".join(CARRY_MODES)}')
    return mode


def path_classes(repo: Path, rev: str, strict: bool = False) -> dict[str, list[str]]:
    """PATH_CLASSES with the overrides of the project config at rev. In strict mode a configured `appInputs` list
    only adds to the defaults, so a project cannot shrink it."""
    classes = {name: list(prefixes) for name, prefixes in PATH_CLASSES.items()}
    overrides = qa_config(repo, rev).get('rerunPaths')
    if overrides is None:
        return classes
    if not isinstance(overrides, dict) or set(overrides) - set(classes):
        raise ContractError(f'{rev}:{CONFIG}: qa.rerunPaths must hold only {", ".join(classes)}')
    for name, prefixes in overrides.items():
        if not (isinstance(prefixes, list) and all(isinstance(p, str) and p and not repo_path_error(p) for p in prefixes)):
            raise ContractError(f'{rev}:{CONFIG}: qa.rerunPaths.{name} must be a list of repository paths')
        classes[name] = prefixes
    if strict:
        classes['appInputs'] = list(dict.fromkeys(PATH_CLASSES['appInputs'] + classes['appInputs']))
    return classes


def classify(paths: list[str], classes: dict[str, list[str]], strict: bool = False) -> dict[str, list[str]]:
    """{app, test, process, ci, docs, other: paths}; app inputs win over the other classes. Classic mode: any `*.md`
    is docs and process paths are no class. Strict mode: process paths are their own class and only root Markdown is
    docs outside `docPaths`."""
    out: dict[str, list[str]] = {'app': [], 'test': [], 'process': [], 'ci': [], 'docs': [], 'other': []}
    for path in paths:
        markdown = path.endswith('.md') and ('/' not in path if strict else True)
        if under(path, classes['appInputs']):
            out['app'].append(path)
        elif under(path, classes['testPaths']):
            out['test'].append(path)
        elif strict and under(path, classes['processPaths']):
            out['process'].append(path)
        elif under(path, classes['ciPaths']):
            out['ci'].append(path)
        elif under(path, classes['docPaths']) or markdown:
            out['docs'].append(path)
        else:
            out['other'].append(path)
    return out
