"""Linear adapter of the harness: an idempotent wrapper around the `linear` CLI (schpet/linear-cli 2.6.0).

    python3 -B tools/apptrick_linear.py [--config .ai/agentic.config.json] [--verbose] <command> [options]

Read-only commands: auth-check, states, git-automation, get-issue, search-issues, list-comments.
Write commands: ensure-project, ensure-label, ensure-taxonomy, ensure-milestone, create-issue, sub-issue,
transition-issue, assign-issue, add-label, remove-label, upsert-comment.

In an app the tool is .ai/scripts/apptrick_linear.py and its contract .ai/trackers/linear-adapter.md; in the harness
repository they are tools/apptrick_linear.py and trackers/linear.md. Every command prints one JSON object on stdout. Errors print one JSON object on
stderr. Exit codes: 0 done, 1 check failed, 2 refused before any write (SEARCH_UNAVAILABLE included), 3 CLI failure,
4 uncertain write: the write was sent but is unconfirmed (it failed, timed out or did not read back). Never replay
an uncertain write; read Linear first.

Writes are idempotent: each one reads first and returns the existing object (`"created": false`) or makes no
change (`"changed": false`). Searches read every page; an incomplete search refuses instead of reporting "not found". Names that differ only in case, spacing
or punctuation are near-duplicates and refuse. Reads are retried for readback; writes are never retried.

Credentials stay in the CLI's keyring (or LINEAR_API_KEY in the environment for CI). The tool never reads or
prints a credential, refuses an argument that looks like one, and redacts tokens and e-mail addresses from every
message it prints."""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# The approved Linear scope (workspace, team, state IDs, key pattern) is the project config's, which an overlay or the
# app supplies and check_harness pins; the core sets none of it.
WORKSPACE_KEY = re.compile(r'[a-z0-9][a-z0-9-]*')
TEAM_KEY = re.compile(r'[A-Z][A-Z0-9]*')
SCOPE_HINT = 'set it in .ai/agentic.config.json or install an overlay that sets it'
ROLES = ('backlog', 'ready', 'inProgress', 'review', 'qa', 'done', 'canceled')
ROUTES = ('app', 'template', 'lab')
TERMINAL_TYPES = {'completed', 'canceled', 'duplicate'}
GIT_EVENTS = ('draft', 'start', 'review', 'mergeable', 'merge')  # Linear's GitAutomationStates enum
WRITES = {('project', 'create'), ('label', 'create'), ('milestone', 'create'), ('issue', 'create'),
          ('issue', 'update'), ('issue', 'comment', 'add'), ('issue', 'comment', 'update')}
MIN_CLI = (2, 6, 0)
# Flags the adapter relies on, checked against the installed CLI's help by auth-check.
SURFACE: dict[tuple[str, ...], tuple[str, ...]] = {
    ('issue', 'create'): ('--team', '--project', '--title', '--state', '--label', '--milestone', '--parent',
                          '--description-file', '--no-interactive', '--no-use-default-template'),
    ('issue', 'update'): ('--state', '--assignee', '--add-label', '--remove-label'),
    ('issue', 'comment', 'add'): ('--body-file',),
    ('issue', 'comment', 'update'): ('--body-file',),
    ('project', 'create'): ('--team', '--name', '--status', '--description', '--json'),
    ('label', 'create'): ('--name', '--team', '--color', '--description'),
    ('milestone', 'create'): ('--project', '--name', '--description', '--target-date'),
    ('team', 'states'): ('--json',),
    ('api',): ('--variables-json',),
}
SECRET = re.compile(r'lin_(?:api|oauth)_[A-Za-z0-9_-]+|(?i:bearer)\s+[A-Za-z0-9._~+/=-]{20,}')
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
ANSI = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]')
COLOR = re.compile(r'#[0-9A-Fa-f]{6}')
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
READBACK_DELAYS = (0.0, 1.0, 2.0)  # seconds before each readback read
PAGE_SIZE = 100
MAX_PAGES = 50
TIMEOUT = 120
# The stable token of the edition's run-ownership comment (claim-pr.md); upsert-comment's default marker.
OWNERSHIP_MARKER = '`apptrick-run-ownership`'

Q_VIEWER = 'query AdapterViewer { viewer { id } }'
Q_SEARCH = ('query AdapterIssueSearch($filter: IssueFilter!, $first: Int!, $after: String) { issues(first: $first, '
            'after: $after, filter: $filter) { nodes { id identifier title url parent { identifier } '
            'state { id name type } } pageInfo { hasNextPage endCursor } } }')
Q_COMMENTS = ('query AdapterComments($id: String!, $first: Int!, $after: String) { issue(id: $id) { '
              'comments(first: $first, after: $after) { nodes { id body createdAt updatedAt user { id } } '
              'pageInfo { hasNextPage endCursor } } } }')
Q_AUTH = 'query AdapterAuth($team: String!) { viewer { id } organization { urlKey } team(id: $team) { id key } }'
Q_GIT = ('query AdapterGitAutomation($team: String!) { team(id: $team) { gitAutomationStates(first: 100) '
         '{ nodes { id event state { id name } targetBranch { branchPattern isRegex } } } } '
         'integrations(first: 100) { nodes { id service } } viewer { admin } }')
Q_PROJECTS = ('query AdapterProjects($first: Int!, $after: String) { projects(first: $first, after: $after, '
              'includeArchived: true) { nodes { id name url archivedAt teams { nodes { key } } } '
              'pageInfo { hasNextPage endCursor } } }')
Q_PROJECT = ('query AdapterProject($id: String!, $first: Int!, $after: String) { project(id: $id) { id name url '
             'archivedAt teams { nodes { key } } '
             'projectMilestones(first: $first, after: $after, includeArchived: true) '
             '{ nodes { id name archivedAt } pageInfo { hasNextPage endCursor } } } }')
Q_LABELS = ('query AdapterLabels($team: String!, $first: Int!, $after: String) { issueLabels(first: $first, '
            'after: $after, includeArchived: true, filter: { or: [{ team: { key: { eq: $team } } }, '
            '{ team: { null: true } }] }) { nodes { id name isGroup archivedAt team { key } } '
            'pageInfo { hasNextPage endCursor } } }')
Q_ISSUES_BY_TITLE = ('query AdapterIssuesByTitle($project: ID!, $title: String!, $first: Int!, $after: String) '
                     '{ issues(first: $first, after: $after, filter: { project: { id: { eq: $project } }, '
                     'title: { eqIgnoreCase: $title } }) { nodes { id identifier title parent { identifier } } '
                     'pageInfo { hasNextPage endCursor } } }')
Q_HISTORY = ('query AdapterHistory($id: String!) { issue(id: $id) { history(first: 50) { nodes { createdAt '
             'fromState { id name } toState { id name } } } } }')
Q_ISSUE = ('query AdapterIssue($id: String!) { issue(id: $id) { id identifier title url archivedAt team { key } '
           'project { id } parent { identifier } state { id name type } labels { nodes { name } } '
           'projectMilestone { id name } assignee { id } } }')


class AdapterError(Exception):
    label = 'ERROR'
    code = 3

    def __init__(self, message: str, command: str | None = None):
        super().__init__(message)
        self.command = command


class CheckFailed(AdapterError):
    label, code = 'CHECK_FAILED', 1


class Refused(AdapterError):
    label, code = 'REFUSED', 2


class SearchUnavailable(Refused):
    label = 'SEARCH_UNAVAILABLE'


class ScopeMissing(Refused):
    """The config leaves a Linear scope value (workspace, team, team ID, a state ID, the key pattern) unset."""
    label = 'LINEAR_SCOPE_MISSING'


class CliFailed(AdapterError):
    label, code = 'CLI_FAILED', 3


class Uncertain(AdapterError):
    label, code = 'UNCERTAIN_WRITE', 4


def redact(text: str) -> str:
    return EMAIL.sub('[email]', SECRET.sub('[REDACTED]', text))


def require(condition: object, message: str) -> None:
    if not condition:
        raise Refused(message)


def is_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def normalise(name: str) -> str:
    """Comparison key for near-duplicates: case, spacing and punctuation ignored."""
    return re.sub(r'[\W_]+', '', name.casefold())


def clean_text(value: str, what: str, limit: int = 255) -> str:
    value = value.strip()
    require(value, f'{what} is empty')
    require(len(value) <= limit, f'{what} is longer than {limit} characters')
    require(not re.search(r'[\x00-\x1f\x7f]', value), f'{what} contains a control character')
    require(not SECRET.search(value), f'{what} looks like it contains a credential')
    return value


@dataclass
class Config:
    workspace: str
    team: str
    team_id: str
    project: str | None
    states: dict[str, dict[str, str]]
    routing: dict[str, str | None]
    key_pattern: re.Pattern[str]

    def allowed_projects(self) -> set[str]:
        return {value for value in self.routing.values() if value}

    def route(self, name: str) -> str:
        project = self.routing.get(name)
        if not project:
            raise Refused(f'linear.routing.{name} is not set; run ensure-project and bind the app first')
        return project

    def role_of(self, state_id: str) -> str | None:
        return next((role for role, state in self.states.items() if state['id'] == state_id), None)


def load_config(path: str | Path) -> Config:
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise Refused(f'cannot read config {path}: {type(error).__name__}')
    linear = raw.get('linear') if isinstance(raw, dict) else None
    require(isinstance(linear, dict), 'config has no linear block')
    assert isinstance(linear, dict)
    def scope(value: Any, where: str) -> Any:
        if value is None:
            raise ScopeMissing(f'{where} is not set; {SCOPE_HINT}')
        return value
    workspace = scope(linear.get('workspace'), 'linear.workspace')
    require(isinstance(workspace, str) and WORKSPACE_KEY.fullmatch(workspace),
            'linear.workspace must be a Linear workspace URL key')
    team = scope(linear.get('team'), 'linear.team')
    require(isinstance(team, str) and TEAM_KEY.fullmatch(team), 'linear.team must be a Linear team key')
    require(is_uuid(scope(linear.get('teamId'), 'linear.teamId')), 'linear.teamId must be a UUID')
    project = linear.get('project')
    require(project is None or is_uuid(project), 'linear.project must be a UUID or null')
    states = linear.get('states')
    require(isinstance(states, dict) and set(states) == set(ROLES),
            'linear.states must map exactly these roles: ' + ', '.join(ROLES))
    assert isinstance(states, dict)
    for role in ROLES:
        state = states[role]
        if isinstance(state, dict):
            scope(state.get('id'), f'linear.states.{role}.id')
        require(isinstance(state, dict) and is_uuid(state.get('id')) and isinstance(state.get('name'), str)
                and isinstance(state.get('type'), str), f'linear.states.{role} needs id (UUID), name and type')
    names = [states[role]['name'] for role in ROLES]
    require(len(set(names)) == len(names), 'linear.states names must be unique')
    routing = linear.get('routing')
    require(isinstance(routing, dict) and set(routing) == set(ROUTES),
            'linear.routing must have exactly these keys: ' + ', '.join(ROUTES))
    assert isinstance(routing, dict)
    for name in ROUTES:
        require(routing[name] is None or is_uuid(routing[name]), f'linear.routing.{name} must be a UUID or null')
    require(routing['app'] == project, 'linear.routing.app must equal linear.project')
    pattern = scope(raw.get('ticketKeyPattern'), 'ticketKeyPattern')
    require(isinstance(pattern, str) and pattern.startswith(team + '-'), f'ticketKeyPattern must start with {team}-')
    assert isinstance(pattern, str)
    return Config(workspace, team, linear['teamId'], project,
                  {role: {k: states[role][k] for k in ('id', 'name', 'type')} for role in ROLES},
                  dict(routing), re.compile(pattern))


class Linear:
    """Runs the CLI with the approved workspace first, no prompts, no colour and no .env file."""

    def __init__(self, workspace: str, verbose: bool = False):
        cli = os.environ.get('APPTRICK_LINEAR_CLI') or shutil.which('linear')
        if not cli:
            raise CheckFailed('the linear CLI is not installed: https://github.com/schpet/linear-cli')
        self.cli = cli
        self.workspace = workspace
        self.verbose = verbose
        self.written: str | None = None  # the redacted command of a write that ran in this invocation

    def shown(self, args: tuple[str, ...]) -> str:
        return redact(' '.join(shlex.quote(a) for a in ('linear', '--workspace', self.workspace, *args)))

    def run(self, *args: str) -> str:
        shown = self.shown(args)
        for arg in args:
            if SECRET.search(arg):
                raise Refused('an argument looks like a credential; credentials never go in argv', shown)
        if self.verbose:
            print('+ ' + shown, file=sys.stderr)
        if (tuple(args[:2]) in WRITES or tuple(args[:3]) in WRITES) and '--help' not in args:
            self.written = shown  # set before the run: a failed or timed-out write may still have reached Linear
        env = dict(os.environ, LINEAR_IGNORE_ENV_FILE='1', NO_COLOR='1')
        try:
            result = subprocess.run([self.cli, '--workspace', self.workspace, *args], capture_output=True, text=True,
                                    stdin=subprocess.DEVNULL, env=env, timeout=TIMEOUT)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CliFailed(f'the CLI did not run: {type(error).__name__}', shown)
        if result.returncode:
            detail = ANSI.sub('', (result.stderr.strip() or result.stdout.strip()))[-600:]
            raise CliFailed(f'exit {result.returncode}: {redact(detail)}', shown)
        return ANSI.sub('', result.stdout)

    def gql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        out = self.run('api', query, '--variables-json', json.dumps(variables))
        try:
            body = json.loads(out)
        except ValueError:
            raise CliFailed('the API answer is not JSON', self.shown(('api', query.split('(')[0])))
        if body.get('errors') or not isinstance(body.get('data'), dict):
            messages = '; '.join(str(e.get('message')) for e in body.get('errors') or [])
            raise CliFailed('GraphQL error: ' + redact(messages), self.shown(('api', query.split('(')[0])))
        return body['data']

    def pages(self, query: str, variables: dict[str, Any],
              path: tuple[str, ...]) -> tuple[dict[str, Any], list[Any]] | None:
        """(first page's data, every node of one connection); None when the connection's parent does not exist."""
        nodes: list[Any] = []
        first: dict[str, Any] | None = None
        after = None
        for _ in range(MAX_PAGES):
            page = self.gql(query, {**variables, 'first': PAGE_SIZE, 'after': after})
            first = first or page
            data: Any = page
            for key in path:
                data = data.get(key) if isinstance(data, dict) else None
            if data is None:
                return None
            nodes += data['nodes']
            info = data['pageInfo']
            if not info['hasNextPage']:
                return first, nodes
            after = info['endCursor']
        raise SearchUnavailable(f'{path[-1]} has more than {MAX_PAGES} pages; the search is incomplete')


def readback(fetch: Callable[[], Any], ok: Callable[[Any], bool]) -> Any:
    value = None
    for delay in READBACK_DELAYS:
        time.sleep(delay)
        value = fetch()
        if ok(value):
            return value
    return value


def all_nodes(found: tuple[dict[str, Any], list[Any]] | None) -> list[Any]:
    return found[1] if found else []


# ---- reads ---------------------------------------------------------------------------------------------------------

def team_keys(node: dict[str, Any]) -> list[str]:
    return [team['key'] for team in node['teams']['nodes']]


def live_states(cfg: Config, linear: Linear) -> list[dict[str, Any]]:
    try:
        nodes = json.loads(linear.run('team', 'states', cfg.team, '--json'))['nodes']
    except (ValueError, KeyError, TypeError):
        raise CliFailed('team states did not return JSON nodes', linear.shown(('team', 'states', cfg.team, '--json')))
    nodes = sorted(nodes, key=lambda n: n.get('position', 0))
    return [{'id': n['id'], 'name': n['name'], 'type': n['type']} for n in nodes]


def state_mismatches(cfg: Config, observed: list[dict[str, Any]]) -> list[str]:
    by_id = {state['id']: state for state in observed}
    out = []
    for role in ROLES:
        want = cfg.states[role]
        got = by_id.get(want['id'])
        if got is None:
            out.append(f'{role}: state {want["id"]} ({want["name"]}) is not a {cfg.team} state')
        elif (got['name'], got['type']) != (want['name'], want['type']):
            out.append(f'{role}: expected {want["name"]}/{want["type"]}, Linear has {got["name"]}/{got["type"]}')
    return out


def read_project(linear: Linear, project_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    found = linear.pages(Q_PROJECT, {'id': project_id}, ('project', 'projectMilestones'))
    require(found is not None, f'project {project_id} does not exist')
    assert found is not None
    return found[0]['project'], found[1]


def routed_project(cfg: Config, linear: Linear, project_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """A project the routing allows, read back and checked to be an active project of the team."""
    require(project_id in cfg.allowed_projects(), f'project {project_id} is not in linear.routing; refusing')
    project, milestones = read_project(linear, project_id)
    require(cfg.team in team_keys(project), f'project {project_id} is not in team {cfg.team}')
    require(not project['archivedAt'], f'project {project_id} is archived')
    return project, milestones


def read_issue(cfg: Config, linear: Linear, key: str) -> dict[str, Any]:
    require(cfg.key_pattern.fullmatch(key), f'{key!r} does not match ticketKeyPattern {cfg.key_pattern.pattern}')
    issue = linear.gql(Q_ISSUE, {'id': key})['issue']
    require(issue, f'issue {key} does not exist')
    require(issue['team']['key'] == cfg.team, f'issue {key} is not in team {cfg.team}')
    return issue


def summary(cfg: Config, issue: dict[str, Any]) -> dict[str, Any]:
    state = issue['state']
    return {'identifier': issue['identifier'], 'id': issue['id'], 'title': issue['title'], 'url': issue['url'],
            'project': (issue['project'] or {}).get('id'), 'parent': (issue['parent'] or {}).get('identifier'),
            'state': {'role': cfg.role_of(state['id']), 'name': state['name'], 'id': state['id']},
            'labels': sorted(label['name'] for label in issue['labels']['nodes']),
            'milestone': issue['projectMilestone'], 'assignee': (issue['assignee'] or {}).get('id'),
            'archived': bool(issue['archivedAt'])}


def writable_issue(cfg: Config, linear: Linear, key: str) -> dict[str, Any]:
    """An issue this repository may change: in the bound team, not archived, in a project of linear.routing."""
    issue = read_issue(cfg, linear, key)
    require(not issue['archivedAt'], f'issue {key} is archived')
    require((issue['project'] or {}).get('id') in cfg.allowed_projects(),
            f'issue {key} is outside the projects in linear.routing; it is read-only here')
    return issue


def viewer_id(linear: Linear) -> str:
    """The credential's user ID from the API (`auth whoami` is never used: it prints a name and e-mail address)."""
    return linear.gql(Q_VIEWER, {})['viewer']['id']


def team_labels(linear: Linear, cfg: Config) -> list[dict[str, Any]]:
    return all_nodes(linear.pages(Q_LABELS, {'team': cfg.team}, ('issueLabels',)))


def labels_named(linear: Linear, cfg: Config, name: str,
                 labels: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    labels = team_labels(linear, cfg) if labels is None else labels
    near = [l for l in labels if normalise(l['name']) == normalise(name) and l['name'].casefold() != name.casefold()]
    require(not near, 'near-duplicate label names exist: ' + ', '.join(f'{l["name"]!r} {l["id"]}' for l in near))
    return [label for label in labels if label['name'].casefold() == name.casefold()]


def usable_label(matches: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    active = [label for label in matches if not label['archivedAt']]
    if not active:
        require(not matches, f'label {name!r} exists only archived; restoring it is the owner\'s decision')
        return None
    if len(active) > 1:
        exact = [label for label in active if label['name'] == name]
        require(len(exact) == 1, f'label {name!r} is ambiguous: ' + ', '.join(l['id'] for l in active))
        active = exact
    label = active[0]
    require(not label['isGroup'], f'label {name!r} is a label group and cannot be applied to an issue')
    return label


# ---- commands ------------------------------------------------------------------------------------------------------

def cmd_auth_check(cfg: Config, linear: Linear, _: argparse.Namespace) -> dict[str, Any]:
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', linear.run('--version'))
    if not match:
        raise CheckFailed('cannot read the CLI version')
    version = tuple(int(part) for part in match.groups())
    if version < MIN_CLI:
        raise CheckFailed(f'linear {".".join(map(str, version))} is older than {".".join(map(str, MIN_CLI))}')
    for command, flags in SURFACE.items():
        text = linear.run(*command, '--help')
        missing = [flag for flag in flags if not re.search(re.escape(flag) + r'(?![\w-])', text)]
        if missing:
            raise CheckFailed(f'linear {" ".join(command)} lacks {", ".join(missing)}; upgrade the CLI')
    data = linear.gql(Q_AUTH, {'team': cfg.team_id})
    if (data.get('organization') or {}).get('urlKey') != cfg.workspace:
        raise CheckFailed(f'the credential is not for workspace {cfg.workspace}')
    team = data.get('team') or {}
    if team.get('id') != cfg.team_id or team.get('key') != cfg.team:
        raise CheckFailed(f'team {cfg.team_id} is not {cfg.team} in this workspace')
    return {'ok': True, 'cli': '.'.join(map(str, version)), 'workspace': cfg.workspace, 'team': cfg.team,
            'teamId': cfg.team_id, 'viewerId': data['viewer']['id']}


def cmd_states(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    observed = live_states(cfg, linear)
    mismatches = state_mismatches(cfg, observed)
    if args.observed_out:
        record = {'observedAt': time.strftime('%Y-%m-%d'), 'workspace': cfg.workspace, 'team': cfg.team,
                  'teamId': cfg.team_id, 'states': observed}
        Path(args.observed_out).write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
    return {'ok': not mismatches, 'team': cfg.team, 'map': cfg.states, 'observed': observed,
            'mismatches': mismatches}


MANUAL_GIT_STEP = ('In Linear: Settings > Team > Workflows & automations > Pull request and commit automations '
                   '(the bound team). Set every event to "No action", also for every target-branch rule, then run '
                   'git-automation again. The adapter does not change team settings.')


def cmd_git_automation(cfg: Config, linear: Linear, _: argparse.Namespace) -> dict[str, Any]:
    """ok only when nothing can move an issue on a Git event. Without an explicit rule, an installed Git integration
    applies Linear's default move for that event; a default rule with no state is the explicit "No action".
    Only a workspace admin is sure to see every integration, so a non-admin credential fails the check."""
    data = linear.gql(Q_GIT, {'team': cfg.team_id})
    admin = data['viewer']['admin'] is True
    rules = [{'id': r['id'], 'event': r['event'], 'state': (r['state'] or {}).get('name'),
              'targetBranch': (r['targetBranch'] or {}).get('branchPattern')}
             for r in data['team']['gitAutomationStates']['nodes']]
    active = [rule for rule in rules if rule['state'] is not None]
    services = sorted({i['service'] for i in data['integrations']['nodes']})
    git = [s for s in services if s.lower().startswith(('github', 'gitlab'))]
    no_action = {r['event'] for r in rules if r['targetBranch'] is None and r['state'] is None}
    default_moves = [event for event in GIT_EVENTS if event not in no_action] if git else []
    ok = admin and not active and not default_moves
    result: dict[str, Any] = {'ok': ok, 'team': cfg.team, 'viewerAdmin': admin, 'gitIntegrations': git,
                              'rules': rules, 'activeRules': active, 'defaultMoves': default_moves}
    if not admin:
        result['message'] = ('the credential is not a workspace admin, so integrations may be hidden; '
                             'run git-automation with an admin credential')
    if active or default_moves:
        result['manualStep'] = MANUAL_GIT_STEP
    return result


def cmd_get_issue(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    return {'ok': True, 'issue': summary(cfg, read_issue(cfg, linear, args.issue))}


def cmd_ensure_project(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    name = clean_text(args.name, 'project name', 80)
    description = clean_text(args.description, 'description') if args.description else None

    def lookup() -> list[dict[str, Any]]:
        projects = all_nodes(linear.pages(Q_PROJECTS, {}, ('projects',)))
        near = [p for p in projects if normalise(p['name']) == normalise(name) and p['name'] != name]
        require(not near, f'near-duplicate project names exist: ' + ', '.join(f'{p["name"]!r} {p["id"]}' for p in near))
        exact = [p for p in projects if p['name'] == name]
        require(len(exact) <= 1, f'project name {name!r} is ambiguous: ' + ', '.join(p['id'] for p in exact))
        for project in exact:
            require(cfg.team in team_keys(project), f'project {name!r} exists outside team {cfg.team}: {project["id"]}')
            require(not project['archivedAt'], f'project {name!r} is archived ({project["id"]}); '
                                               'unarchiving is the owner\'s decision')
        return exact

    def shape(p: dict[str, Any]) -> dict[str, Any]:
        return {'id': p['id'], 'name': p['name'], 'url': p['url'], 'teams': team_keys(p)}

    found = lookup()
    if found:
        return {'ok': True, 'created': False, 'project': shape(found[0])}
    command = ['project', 'create', '--team', cfg.team, '--name', name, '--status', args.status, '--json']
    if description:
        command += ['--description', description]
    linear.run(*command)
    found = readback(lookup, bool)
    if not found:
        raise Uncertain(f'project create ran but project {name!r} is not readable; do not replay, search Linear',
                        linear.shown(tuple(command)))
    return {'ok': True, 'created': True, 'project': shape(found[0])}


def label_shape(label: dict[str, Any]) -> dict[str, Any]:
    return {'id': label['id'], 'name': label['name'], 'team': (label['team'] or {}).get('key')}


def create_label(cfg: Config, linear: Linear, name: str, color: str | None,
                 description: str | None) -> dict[str, Any]:
    command = ['label', 'create', '--name', name, '--team', cfg.team]
    if color:
        command += ['--color', color]
    if description:
        command += ['--description', description]
    linear.run(*command)
    matches = readback(lambda: labels_named(linear, cfg, name), lambda found: any(not l['archivedAt'] for l in found))
    label = usable_label(matches, name) if matches else None
    if not label:
        raise Uncertain(f'label create ran but label {name!r} is not readable; do not replay, search Linear',
                        linear.shown(tuple(command)))
    return label


def cmd_ensure_label(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    name = clean_text(args.name, 'label name', 80)
    require(args.color is None or COLOR.fullmatch(args.color), 'color must be #RRGGBB')
    description = clean_text(args.description, 'description') if args.description else None
    label = usable_label(labels_named(linear, cfg, name), name)
    if label:
        return {'ok': True, 'created': False, 'label': label_shape(label)}
    return {'ok': True, 'created': True, 'label': label_shape(create_label(cfg, linear, name, args.color, description))}


def taxonomy(path: str | Path) -> tuple[bool, list[str]]:
    """(labels.enabled, every label name of the config's labels.* lists, first spelling of each name kept)."""
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise Refused(f'cannot read config {path}: {type(error).__name__}')
    labels = raw.get('labels') if isinstance(raw, dict) else None
    require(isinstance(labels, dict), 'config has no labels block')
    assert isinstance(labels, dict)
    enabled = labels.get('enabled', True)
    require(isinstance(enabled, bool), 'labels.enabled must be true or false')
    names: list[str] = []
    for group, values in labels.items():
        if group == 'enabled':
            continue
        require(isinstance(values, list) and all(isinstance(v, str) for v in values),
                f'labels.{group} must be a list of label names')
        for value in values:
            name = clean_text(value, f'labels.{group} name', 80)
            if name.casefold() not in {n.casefold() for n in names}:
                names.append(name)
    return bool(enabled), names


def cmd_ensure_taxonomy(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    """ensure-label for every name in the config's labels.* taxonomy. Every refusal happens before the first write."""
    enabled, names = taxonomy(args.config)
    if not enabled:
        return {'ok': True, 'enabled': False, 'created': 0, 'labels': []}
    require(names, 'the labels taxonomy is empty')
    keys = [normalise(name) for name in names]
    duplicates = sorted({name for name, key in zip(names, keys) if keys.count(key) > 1})
    require(not duplicates, 'the taxonomy has near-duplicate names: ' + ', '.join(duplicates))
    existing = team_labels(linear, cfg)
    plan = [(name, usable_label(labels_named(linear, cfg, name, existing), name)) for name in names]
    results = []
    for name, label in plan:
        created = label is None
        if label is None:
            label = create_label(cfg, linear, name, None, None)
        results.append({'name': name, 'created': created, 'label': label_shape(label)})
    return {'ok': True, 'enabled': True, 'created': sum(r['created'] for r in results), 'labels': results}


def cmd_ensure_milestone(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    name = clean_text(args.name, 'milestone name', 80)
    require(args.target_date is None or DATE.fullmatch(args.target_date), 'target date must be YYYY-MM-DD')
    description = clean_text(args.description, 'description') if args.description else None
    project_id = cfg.route(args.route)
    routed_project(cfg, linear, project_id)

    def lookup() -> list[dict[str, Any]]:
        _, milestones = read_project(linear, project_id)
        near = [m for m in milestones if normalise(m['name']) == normalise(name) and m['name'] != name]
        require(not near, 'near-duplicate milestone names exist: ' + ', '.join(f'{m["name"]!r}' for m in near))
        exact = [m for m in milestones if m['name'] == name]
        require(len(exact) <= 1, f'milestone {name!r} is ambiguous')
        require(not any(m['archivedAt'] for m in exact), f'milestone {name!r} is archived')
        return exact

    found = lookup()
    if found:
        return {'ok': True, 'created': False, 'project': project_id,
                'milestone': {'id': found[0]['id'], 'name': found[0]['name']}}
    command = ['milestone', 'create', '--project', project_id, '--name', name]
    if description:
        command += ['--description', description]
    if args.target_date:
        command += ['--target-date', args.target_date]
    linear.run(*command)
    found = readback(lookup, bool)
    if not found:
        raise Uncertain(f'milestone create ran but {name!r} is not readable; do not replay, search Linear',
                        linear.shown(tuple(command)))
    return {'ok': True, 'created': True, 'project': project_id,
            'milestone': {'id': found[0]['id'], 'name': found[0]['name']}}


def create_issue(cfg: Config, linear: Linear, args: argparse.Namespace, project_id: str,
                 milestones: list[dict[str, Any]], parent: str | None) -> dict[str, Any]:
    title = clean_text(args.title, 'title')
    state = cfg.states[args.state]
    labels = []
    for requested in args.label or []:
        label = usable_label(labels_named(linear, cfg, clean_text(requested, 'label name', 80)), requested)
        require(label, f'label {requested!r} does not exist; run ensure-label first')
        assert label is not None
        labels.append(label['name'])
    milestone = None
    if args.milestone:
        found = [m for m in milestones if m['name'] == args.milestone and not m['archivedAt']]
        require(len(found) == 1, f'milestone {args.milestone!r} does not exist in the project; run ensure-milestone')
        milestone = found[0]['id']
    if args.description_file:
        try:
            body = Path(args.description_file).read_text()
        except (OSError, UnicodeDecodeError) as error:
            raise Refused(f'cannot read the description file: {type(error).__name__}')
        require(not SECRET.search(body), 'the description file looks like it contains a credential')

    def lookup() -> list[dict[str, Any]]:
        found = all_nodes(linear.pages(Q_ISSUES_BY_TITLE, {'project': project_id, 'title': title}, ('issues',)))
        found = [i for i in found if (i['parent'] or {}).get('identifier') == parent]
        near = [i for i in found if i['title'] != title]
        require(not near, 'near-duplicate issue titles exist: ' + ', '.join(i['identifier'] for i in near))
        require(len(found) <= 1, f'title {title!r} is ambiguous: ' + ', '.join(i['identifier'] for i in found))
        return found

    found = lookup()
    if found:
        return {'ok': True, 'created': False, 'issue': summary(cfg, read_issue(cfg, linear, found[0]['identifier']))}
    command = ['issue', 'create', '--team', cfg.team, '--project', project_id, '--title', title,
               '--state', state['name'], '--no-interactive', '--no-use-default-template']
    if args.description_file:
        command += ['--description-file', str(args.description_file)]
    for label in labels:
        command += ['--label', label]
    if milestone:
        command += ['--milestone', milestone]
    if parent:
        command += ['--parent', parent]
    linear.run(*command)
    found = readback(lookup, bool)
    if not found:
        raise Uncertain(f'issue create ran but {title!r} is not readable; do not replay, search Linear',
                        linear.shown(tuple(command)))
    issue = summary(cfg, read_issue(cfg, linear, found[0]['identifier']))
    problems = []
    if issue['project'] != project_id:
        problems.append('project')
    if issue['parent'] != parent:
        problems.append('parent')
    if issue['state']['id'] != state['id']:
        problems.append('state')
    if not set(labels) <= set(issue['labels']):
        problems.append('labels')
    if milestone and (issue['milestone'] or {}).get('id') != milestone:
        problems.append('milestone')
    if problems:
        raise Uncertain(f'{issue["identifier"]} was created but its readback differs in: {", ".join(problems)}',
                        linear.shown(tuple(command)))
    return {'ok': True, 'created': True, 'issue': issue}


def cmd_create_issue(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    project_id = cfg.route(args.route)
    _, milestones = routed_project(cfg, linear, project_id)
    return create_issue(cfg, linear, args, project_id, milestones, None)


def cmd_sub_issue(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    parent = read_issue(cfg, linear, args.parent)
    project_id = (parent['project'] or {}).get('id')
    require(isinstance(project_id, str), f'parent {args.parent} has no project')
    assert isinstance(project_id, str)
    require(not parent['archivedAt'], f'parent {args.parent} is archived')
    _, milestones = routed_project(cfg, linear, project_id)
    return create_issue(cfg, linear, args, project_id, milestones, parent['identifier'])


def history_check(linear: Linear, key: str, before_id: str, target_id: str) -> dict[str, Any]:
    """Best effort: the newest recorded move into the target state should start from the state read before the
    update. Linear usually records the entry after the readback, so the usual result is "unavailable", which is not
    a conflict; "confirmed" and "conflict" appear only when the entry is already there."""
    try:
        nodes = linear.gql(Q_HISTORY, {'id': key})['issue']['history']['nodes']
        entry = next((n for n in nodes if (n.get('toState') or {}).get('id') == target_id), None)
    except (AdapterError, KeyError, TypeError, AttributeError):
        return {'status': 'unavailable'}
    if entry is None:
        return {'status': 'unavailable'}
    recorded = entry.get('fromState') or {}
    if recorded.get('id') != before_id:
        return {'status': 'conflict', 'recordedFrom': recorded.get('name'), 'at': entry.get('createdAt')}
    return {'status': 'confirmed'}


def cmd_transition_issue(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    target = cfg.states[args.to]
    mismatches = state_mismatches(cfg, live_states(cfg, linear))
    require(not mismatches, 'linear.states differs from Linear: ' + '; '.join(mismatches))
    # Read the issue last, right before the update, to keep the window for a concurrent move small.
    issue = read_issue(cfg, linear, args.issue)
    require(not issue['archivedAt'], f'issue {args.issue} is archived')
    project_id = (issue['project'] or {}).get('id')
    require(project_id in cfg.allowed_projects(), f'issue {args.issue} is outside the projects in linear.routing')
    current = issue['state']
    before = {'role': cfg.role_of(current['id']), 'name': current['name'], 'id': current['id']}
    if current['id'] == target['id']:
        return {'ok': True, 'moved': False, 'issue': args.issue, 'from': before, 'to': before}
    if args.from_roles:
        expected = {cfg.states[role]['id'] for role in args.from_roles}
        names = ', '.join(cfg.states[role]['name'] for role in args.from_roles)
        require(current['id'] in expected, f'{args.issue} is in {current["name"]}, not {names}; someone else moved it')
    require(current['type'] not in TERMINAL_TYPES or args.reopen,
            f'{args.issue} is closed ({current["name"]}); pass --reopen to move it out of a closed state')
    command = ('issue', 'update', args.issue, '--state', target['name'])
    linear.run(*command)
    after = readback(lambda: read_issue(cfg, linear, args.issue), lambda i: i['state']['id'] == target['id'])
    if after['state']['id'] != target['id']:
        raise Uncertain(f'{args.issue} reads back as {after["state"]["name"]}, not {target["name"]}; do not replay',
                        linear.shown(command))
    history = history_check(linear, args.issue, current['id'], target['id'])
    return {'ok': history['status'] != 'conflict', 'moved': True, 'issue': args.issue, 'from': before,
            'to': {'role': args.to, 'name': target['name'], 'id': target['id']}, 'history': history}


def cmd_search_issues(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    """Every issue of one routed project (archived ones excluded), optionally only those whose title or description
    contains the query. The search reads every page; an incomplete one is SEARCH_UNAVAILABLE, never "no match"."""
    project_id = cfg.route(args.route)
    routed_project(cfg, linear, project_id)
    query = clean_text(args.query, 'query', 200) if args.query is not None else None
    issue_filter: dict[str, Any] = {'project': {'id': {'eq': project_id}}}
    if query:
        issue_filter['or'] = [{'title': {'containsIgnoreCase': query}},
                              {'description': {'containsIgnoreCase': query}}]
    found = linear.pages(Q_SEARCH, {'filter': issue_filter}, ('issues',))
    if found is None:
        raise SearchUnavailable('the search returned no issue list; the search is incomplete')
    issues = [{'identifier': n['identifier'], 'title': n['title'], 'url': n['url'],
               'parent': (n['parent'] or {}).get('identifier'),
               'state': {'role': cfg.role_of(n['state']['id']), 'name': n['state']['name']}} for n in found[1]]
    issues.sort(key=lambda issue: int(issue['identifier'].rsplit('-', 1)[-1]))
    return {'ok': True, 'project': project_id, 'query': query, 'complete': True, 'count': len(issues),
            'issues': issues}


def cmd_assign_issue(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    """Assign the issue to the credential's own user (the claim's assignee signal)."""
    viewer = viewer_id(linear)
    issue = writable_issue(cfg, linear, args.issue)
    current = (issue['assignee'] or {}).get('id')
    if current == viewer:
        return {'ok': True, 'changed': False, 'issue': args.issue, 'assignee': viewer}
    require(current is None or args.force, f'{args.issue} is assigned to another user ({current}); that is a claim '
                                           'conflict: follow the claim protocol, or pass --force for a takeover')
    command = ('issue', 'update', args.issue, '--assignee', 'self')
    linear.run(*command)
    after = readback(lambda: read_issue(cfg, linear, args.issue), lambda i: (i['assignee'] or {}).get('id') == viewer)
    if (after['assignee'] or {}).get('id') != viewer:
        raise Uncertain(f'{args.issue} does not read back as assigned to the viewer; do not replay', linear.shown(command))
    return {'ok': True, 'changed': True, 'issue': args.issue, 'assignee': viewer, 'previous': current}


def issue_labels(issue: dict[str, Any]) -> list[str]:
    return [label['name'] for label in issue['labels']['nodes']]


def cmd_add_label(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    name = clean_text(args.label, 'label name', 80)
    issue = writable_issue(cfg, linear, args.issue)
    label = usable_label(labels_named(linear, cfg, name), name)
    require(label, f'label {name!r} does not exist; run ensure-label first')
    assert label is not None
    stored = label['name']
    has = lambda i: stored.casefold() in {n.casefold() for n in issue_labels(i)}
    if has(issue):
        return {'ok': True, 'changed': False, 'issue': args.issue, 'labels': sorted(issue_labels(issue))}
    command = ('issue', 'update', args.issue, '--add-label', stored)
    linear.run(*command)
    after = readback(lambda: read_issue(cfg, linear, args.issue), has)
    if not has(after):
        raise Uncertain(f'{args.issue} does not read back with label {stored!r}; do not replay', linear.shown(command))
    return {'ok': True, 'changed': True, 'issue': args.issue, 'labels': sorted(issue_labels(after))}


def cmd_remove_label(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    name = clean_text(args.label, 'label name', 80)
    issue = writable_issue(cfg, linear, args.issue)
    present = [n for n in issue_labels(issue) if n.casefold() == name.casefold()]
    if not present:
        return {'ok': True, 'changed': False, 'issue': args.issue, 'labels': sorted(issue_labels(issue))}
    gone = lambda i: name.casefold() not in {n.casefold() for n in issue_labels(i)}
    command = ('issue', 'update', args.issue, '--remove-label', present[0])
    linear.run(*command)
    after = readback(lambda: read_issue(cfg, linear, args.issue), gone)
    if not gone(after):
        raise Uncertain(f'{args.issue} still reads back with label {present[0]!r}; do not replay',
                        linear.shown(command))
    return {'ok': True, 'changed': True, 'issue': args.issue, 'labels': sorted(issue_labels(after))}


def issue_comments(cfg: Config, linear: Linear, key: str) -> list[dict[str, Any]]:
    """Every comment of the issue, oldest first. An incomplete read is SEARCH_UNAVAILABLE."""
    read_issue(cfg, linear, key)
    found = linear.pages(Q_COMMENTS, {'id': key}, ('issue', 'comments'))
    if found is None:
        raise SearchUnavailable(f'the comments of {key} could not be read; the comment history is incomplete')
    return sorted(found[1], key=lambda c: (c['createdAt'], c['id']))


def comment_text(body: str) -> str:
    """Comparison form of a comment body: line endings, trailing spaces and outer blank lines ignored."""
    return '\n'.join(line.rstrip() for line in body.strip().splitlines())


def cmd_list_comments(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    viewer = viewer_id(linear)
    marker = clean_text(args.marker, 'marker', 200) if args.marker is not None else None
    comments = [c for c in issue_comments(cfg, linear, args.issue) if marker is None or marker in c['body']]
    return {'ok': True, 'issue': args.issue, 'marker': marker, 'complete': True, 'viewerId': viewer,
            'count': len(comments),
            'comments': [{'id': c['id'], 'user': (c['user'] or {}).get('id'),
                          'mine': (c['user'] or {}).get('id') == viewer, 'createdAt': c['createdAt'],
                          'updatedAt': c['updatedAt'], 'body': redact(c['body'])} for c in comments]}


def cmd_upsert_comment(cfg: Config, linear: Linear, args: argparse.Namespace) -> dict[str, Any]:
    """Create the issue's one comment carrying the marker, or update it in place. The run-ownership comment of the
    claim protocol uses the default marker."""
    marker = clean_text(args.marker, 'marker', 200)
    try:
        body = Path(args.body_file).read_text()
    except (OSError, UnicodeDecodeError) as error:
        raise Refused(f'cannot read the body file: {type(error).__name__}')
    require(not SECRET.search(body), 'the body file looks like it contains a credential')
    require(comment_text(body), 'the body file is empty')
    require(marker in body, f'the body file does not contain the marker {marker}')
    viewer = viewer_id(linear)
    writable_issue(cfg, linear, args.issue)

    def marked() -> list[dict[str, Any]]:
        return [c for c in issue_comments(cfg, linear, args.issue) if marker in c['body']]

    found = marked()
    require(len(found) <= 1, f'{len(found)} comments on {args.issue} carry {marker}: ' +
            ', '.join(c['id'] for c in found) + '; resolve the duplicate first')
    if found:
        comment = found[0]
        require((comment['user'] or {}).get('id') == viewer,
                f'the {marker} comment {comment["id"]} belongs to another user; read it and follow the claim protocol')
        if comment_text(comment['body']) == comment_text(body):
            return {'ok': True, 'created': False, 'updated': False, 'issue': args.issue, 'comment': comment['id']}
        command: tuple[str, ...] = ('issue', 'comment', 'update', comment['id'], '--body-file', str(args.body_file))
    else:
        command = ('issue', 'comment', 'add', args.issue, '--body-file', str(args.body_file))
    linear.run(*command)
    written = lambda found: (len(found) == 1 and (found[0]['user'] or {}).get('id') == viewer
                             and comment_text(found[0]['body']) == comment_text(body))
    after = readback(marked, written)
    if not written(after):
        raise Uncertain(f'the {marker} comment on {args.issue} does not read back as written; do not replay',
                        linear.shown(command))
    return {'ok': True, 'created': not found, 'updated': bool(found), 'issue': args.issue, 'comment': after[0]['id']}


def roles_list(value: str) -> tuple[str, ...]:
    roles = tuple(part.strip() for part in value.split(','))
    unknown = [role for role in roles if role not in ROLES]
    if unknown or not roles:
        raise argparse.ArgumentTypeError(f'unknown role(s) {", ".join(unknown)}; choose from {", ".join(ROLES)}')
    return roles


COMMANDS: dict[str, Callable[[Config, Linear, argparse.Namespace], dict[str, Any]]] = {
    'auth-check': cmd_auth_check, 'states': cmd_states, 'git-automation': cmd_git_automation,
    'get-issue': cmd_get_issue, 'ensure-project': cmd_ensure_project, 'ensure-label': cmd_ensure_label,
    'ensure-taxonomy': cmd_ensure_taxonomy, 'ensure-milestone': cmd_ensure_milestone, 'create-issue': cmd_create_issue,
    'sub-issue': cmd_sub_issue, 'transition-issue': cmd_transition_issue, 'search-issues': cmd_search_issues,
    'assign-issue': cmd_assign_issue, 'add-label': cmd_add_label, 'remove-label': cmd_remove_label,
    'list-comments': cmd_list_comments, 'upsert-comment': cmd_upsert_comment,
}


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog='apptrick_linear.py', description='Linear adapter of the harness (trackers/linear.md)')
    top.add_argument('--config', default='.ai/agentic.config.json')
    top.add_argument('--verbose', action='store_true', help='print each redacted CLI command on stderr')
    sub = top.add_subparsers(dest='command', required=True)
    sub.add_parser('auth-check', help='CLI version, command surface, workspace and team')
    states = sub.add_parser('states', help='compare linear.states with the team workflow states')
    states.add_argument('--observed-out', help='also write the observed states to this JSON file')
    sub.add_parser('git-automation', help='report Linear Git automation rules that would move issues (D5)')
    get = sub.add_parser('get-issue')
    get.add_argument('--issue', required=True)
    project = sub.add_parser('ensure-project', help='find or create a team project by exact name')
    project.add_argument('--name', required=True)
    project.add_argument('--description')
    project.add_argument('--status', default='planned', choices=('backlog', 'planned', 'started'))
    label = sub.add_parser('ensure-label', help='find or create a team issue label')
    label.add_argument('--name', required=True)
    label.add_argument('--color')
    label.add_argument('--description')
    sub.add_parser('ensure-taxonomy', help='ensure-label for every name in the config\'s labels.* taxonomy')
    milestone = sub.add_parser('ensure-milestone', help='find or create a milestone in a routed project')
    milestone.add_argument('--route', default='app', choices=ROUTES)
    milestone.add_argument('--name', required=True)
    milestone.add_argument('--description')
    milestone.add_argument('--target-date')
    for name in ('create-issue', 'sub-issue'):
        issue = sub.add_parser(name, help='find or create an issue by exact title' +
                               (' under a parent' if name == 'sub-issue' else ' in a routed project'))
        if name == 'sub-issue':
            issue.add_argument('--parent', required=True)
        else:
            issue.add_argument('--route', default='app', choices=ROUTES)
        issue.add_argument('--title', required=True)
        issue.add_argument('--description-file')
        issue.add_argument('--label', action='append')
        issue.add_argument('--milestone', help='milestone name in the project')
        issue.add_argument('--state', default='backlog', choices=('backlog', 'ready'))
    move = sub.add_parser('transition-issue', help='move an issue to a lifecycle state and read it back')
    move.add_argument('--issue', required=True)
    move.add_argument('--to', required=True, choices=ROLES)
    move.add_argument('--from', dest='from_roles', type=roles_list, metavar='ROLE[,ROLE...]',
                      help='refuse unless the issue is in one of these states (best-effort guard)')
    move.add_argument('--reopen', action='store_true', help='allow moving out of a closed state')
    search = sub.add_parser('search-issues', help='every issue of a routed project, every page read')
    search.add_argument('--route', default='app', choices=ROUTES)
    search.add_argument('--query', help='only issues whose title or description contains this text (any case)')
    assign = sub.add_parser('assign-issue', help='assign an issue to the credential\'s own user')
    assign.add_argument('--issue', required=True)
    assign.add_argument('--force', action='store_true', help='replace another assignee (claim takeover)')
    for name in ('add-label', 'remove-label'):
        change = sub.add_parser(name, help=('add an existing label to' if name == 'add-label' else 'remove a label from')
                                + ' an issue, keeping its other labels')
        change.add_argument('--issue', required=True)
        change.add_argument('--label', required=True)
    comments = sub.add_parser('list-comments', help='every comment of an issue, every page read')
    comments.add_argument('--issue', required=True)
    comments.add_argument('--marker', help='only comments whose body contains this text')
    upsert = sub.add_parser('upsert-comment', help='create or update the one issue comment that carries a marker')
    upsert.add_argument('--issue', required=True)
    upsert.add_argument('--body-file', required=True)
    upsert.add_argument('--marker', default=OWNERSHIP_MARKER,
                        help=f'text that identifies the comment (default {OWNERSHIP_MARKER}, the run-ownership marker)')
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    linear: Linear | None = None
    try:
        cfg = load_config(args.config)
        linear = Linear(cfg.workspace, args.verbose)
        try:
            result = COMMANDS[args.command](cfg, linear, args)
        except (KeyError, TypeError, AttributeError) as error:
            raise CliFailed(f'unexpected CLI or API answer ({type(error).__name__})')
    except AdapterError as error:
        if linear and linear.written and not isinstance(error, Uncertain):
            # A write ran; whatever failed after it, the write's outcome is unconfirmed.
            error = Uncertain(f'the write was sent but not confirmed ({error.label}: {error}); do not replay, '
                              'read Linear first', linear.written)
        report: dict[str, Any] = {'ok': False, 'error': error.label, 'message': redact(str(error))}
        if error.command:
            report['command'] = error.command
        print(json.dumps(report, ensure_ascii=False), file=sys.stderr)
        return error.code
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
