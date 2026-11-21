# Linear adapter contract

This contract defines how the harness reads and writes Linear for the apps it is installed in.
The `apptrick-*` extensions call these operations whenever they move an issue,
search or file a task, claim or release an issue, or provision a project. The
adapter tool runs them through the `linear` CLI
([schpet/linear-cli](https://github.com/schpet/linear-cli), 2.6.0).

## Layout

| File | In an app | In the harness repository |
|---|---|---|
| This contract | `.ai/trackers/linear-adapter.md` | `core/trackers/linear.md` |
| Adapter tool | `.ai/scripts/apptrick_linear.py` | `core/tools/apptrick_linear.py` |
| Observed states | `.ai/trackers/linear-app-states.observed.json` | from an overlay's `trackers/`, when it has one |
| Linear config block | merged into `.ai/agentic.config.json` | `core/templates/agentic.config.linear.json`, then each overlay's |

The commands below use the app paths. The harness installer copies the files
and merges the config block; `check_harness.py` pins them.

In an app, `.ai/trackers/linear.md` is the edition's generic descriptor: the
upstream-shaped operations, close comments and PR delegation to
`.ai/trackers/github.md`. This contract adds the harness operations. Where the
two overlap it wins: issue search, claims (assignee, `in-progress`, the
ownership comment), labels and state moves go through the adapter commands,
never through raw `linear` commands; a missing taxonomy label is created, not
skipped (D6).

## Scope

- One workspace and one team: `linear.workspace`, `linear.team` and
  `linear.teamId` in the config. The core sets none of them; an overlay or the
  app does, and `check_harness.py` pins them. A config that leaves one unset
  refuses with `LINEAR_SCOPE_MISSING` before any CLI call.
- Every CLI call is `linear --workspace <linear.workspace> ...` with stdin closed,
  `LINEAR_IGNORE_ENV_FILE=1` and `NO_COLOR=1`. The tool never runs
  `linear config` and never relies on `.linear.toml`.
- Writes go only to projects named in `linear.routing`. An issue in any other
  project, including another app's project, is read-only for this
  repository.
- Authority (D6): creating projects, milestones, labels and issues, moving
  issue states, and assigning, labeling and commenting on issues in routed
  projects is routine. Deleting or archiving anything in Linear needs the
  owner's approval; the tool has no delete or archive command. The tool never
  edits an existing project, label or milestone; it only finds or creates them.

## Configuration

The app's `.ai/agentic.config.json` carries the harness's Linear config block
(see [Layout](#layout)):

- `linear.workspace`, `linear.team`, `linear.teamId`: the scope above.
- `linear.project`: the app's own project UUID, `null` until the app is bound.
- `linear.states`: the lifecycle role map below, with state names, IDs and types.
- `linear.routing`: `app`, `template` and `lab` project UUIDs. `app` must equal
  `linear.project`.
- `ticketKeyPattern`: `<team>-[0-9]+`, starting with `linear.team` and a
  hyphen. Every issue key the tool accepts must match it in full; anything else
  is refused before a CLI call. Below, `<KEY>-<n>` is such a key.
- `labels`: the app's label taxonomy (`enabled` plus lists of names), read by
  `ensure-taxonomy`.

## Tool

```bash
python3 -B .ai/scripts/apptrick_linear.py [--config .ai/agentic.config.json] [--verbose] <command> [options]
```

Each command prints one JSON object on stdout. An error prints
`{"ok": false, "error": ..., "message": ..., "command": ...}` on stderr.

| Exit | Error | Meaning |
|---|---|---|
| 0 | - | Done |
| 1 | `CHECK_FAILED` | A check found a difference (states, Git automation, CLI surface), or a move's history shows a concurrent move |
| 2 | `REFUSED`, `SEARCH_UNAVAILABLE` | Refused before any write |
| 3 | `CLI_FAILED` | A read through the CLI or API returned an error; the message carries the redacted command |
| 4 | `UNCERTAIN_WRITE` | A write was sent, but nothing confirmed it |

A write counts as sent as soon as its command starts. So a write command that
fails or times out, and any failure after a write (a readback error, a refused
readback or an unexpected API answer), is reported as `UNCERTAIN_WRITE` with
the write's redacted command: the CLI may have failed after Linear applied the
change. A failure or an unexpected answer shape before any write is `CLI_FAILED`.

`UNCERTAIN_WRITE` means: never replay the write. Read Linear first (`get-issue`
or the ensure command again, which only reads when the object exists), then
decide. `SEARCH_UNAVAILABLE` means a search could not read every page; it is
never treated as "not found".

## Auth check

`auth-check` verifies, without writing:

1. The CLI exists and is at least 2.6.0.
2. The help text of every subcommand the adapter uses lists the flags it needs.
3. The stored credential belongs to `linear.workspace`
   (`organization.urlKey`), and `linear.teamId` is team `linear.team`.

It returns the CLI version, scope and the viewer's ID. It does not print the
user's name or e-mail address; `auth whoami` is not used.

## State map

The core fixes the roles, state names and types; the state IDs are the team's
and come with the scope (`linear.states.<role>.id`). `states --observed-out`
records the team's live states; an overlay may install that record as
`.ai/trackers/linear-app-states.observed.json`.

| Role | Linear state | Type |
|---|---|---|
| `backlog` | Backlog | backlog |
| `ready` | Ready | unstarted |
| `inProgress` | In Progress | started |
| `review` | Review | started |
| `qa` | QA | started |
| `done` | Done | completed |
| `canceled` | Canceled | canceled |

A team may also have other states, such as `Duplicate` (type duplicate), which
the harness does not use.
Review, QA and In Progress share the type `started`, so the adapter always moves
by state name and confirms by state ID, never by type.

`states` compares the committed map with the team's live states and fails on a
renamed, retyped or missing state. Run it in set-up and after any workflow
change in Linear; `transition-issue` repeats the comparison before each move.

## Stage moves (D5)

The harness moves every state itself, as `SDLC.md` "Linear states" defines:

| Trigger | Skill | Move |
|---|---|---|
| New issue, Definition of Ready not met / met | `apptrick-create-issue` | created in `backlog` / `ready` |
| Claim | `apptrick-deliver` | `--to inProgress --from backlog,ready` |
| Ready PR open and read back | `apptrick-open-pr` | `--to review --from inProgress` |
| Independent review APPROVE on a `needs-qa` PR | `apptrick-review` | `--to qa --from review` |
| Independent review CHANGES_REQUESTED | `apptrick-review` | `--to inProgress --from review` |
| Merge read back, QA gate satisfied or `skip-qa` | `apptrick-merge` | `--to done` |

`--from` (one role or a comma-separated list) is a best-effort guard, not an
atomic compare-and-set: Linear has no conditional update. The tool reads the
issue right before the update and refuses when it is in none of the expected
states. A move by someone else in the moment between that read and the update
can still be overwritten; the history check below reports it afterwards.

## Issues

### `get-issue`

Reads one issue by key: identifier, title, URL, project, parent, state (role,
name and ID), labels, milestone, assignee ID and archived flag.

### `search-issues`

```bash
apptrick_linear.py search-issues [--route app] [--query "<text>"]
```

The duplicate search before `create-issue`. It lists every issue of the routed
project (archived ones excluded), or only those whose title or description
contains the query, ignoring case. It reads every page and prints
`"complete": true`; a search that cannot read every page is
`SEARCH_UNAVAILABLE`, never an empty result, and stops the create. Run it
without `--query` to read the whole project, then deduplicate by meaning.

### `create-issue`

```bash
apptrick_linear.py create-issue --route app --title "<title>" --description-file <file.md> \
  [--label <name>]... [--milestone <name>] [--state backlog|ready]
```

- The project comes from `linear.routing.<route>` (default `app`): app behavior
  goes to `app`, a shared fix gets a linked issue in `template`, runner and lab
  fixes go to `lab`. An unset route refuses.
- Idempotency key: the exact title among the project's top-level issues. An
  existing issue is returned with `"created": false`, in whatever state it is.
  A title that differs only in case refuses as a near-duplicate; two matches
  refuse as ambiguous.
- Labels must exist (`ensure-label` first); they match without regard to case
  and are passed by their stored name. Label groups refuse. The milestone must
  exist in the project (`ensure-milestone` first).
- The command is `issue create --team <team> --project <uuid> --title ... --state <name>
  --no-interactive --no-use-default-template`, plus `--description-file`,
  `--label`, `--milestone <id>` and `--parent` as given. The description goes by
  file, never in argv, and a file that looks like it holds a credential refuses.
- Readback: the issue is found again by title and read; project, parent, state
  ID, labels and milestone must match, or the result is `UNCERTAIN_WRITE`.

### `sub-issue`

```bash
apptrick_linear.py sub-issue --parent <KEY>-<n> --title "<title>" [same options as create-issue]
```

The project is the parent's project, which must be in `linear.routing`. The
idempotency key is the exact title among that parent's children. The readback
also confirms the parent.

### `transition-issue`

```bash
apptrick_linear.py transition-issue --issue <KEY>-<n> --to <role> [--from <role>[,<role>...]] [--reopen]
```

1. Compare `linear.states` with Linear; a difference refuses.
2. Read the issue; it must be in the bound team, not archived, and in a routed project.
   This read comes last, right before the update.
3. Already in the target state: return `"moved": false` without a write.
4. `--from` given and the issue is in none of those states: refuse.
5. A closed issue (completed, canceled, duplicate) moves only with `--reopen`.
6. `issue update <KEY>-<n> --state "<name>"`, then read back until the state ID
   equals the target (three reads). Otherwise `UNCERTAIN_WRITE`.
7. History check (best effort): the newest history entry into the target state
   should start from the state read in step 2. `"history": {"status": "confirmed"}`
   when it does; `"conflict"` (with `ok: false`, exit 1) when it starts
   elsewhere, meaning someone moved the issue in between; `"unavailable"` when
   Linear has not recorded the entry yet. Linear usually records it after the
   readback, so `"unavailable"` is the usual result and is not a failure;
   `"confirmed"` and `"conflict"` appear only when the entry is already there.
   A conflict is not rolled back; read the issue and decide.

There is no separate close command: closing is `--to done` (or `--to canceled`
for explicitly not planned). The generic descriptor's close-issue comment step
still applies.

## Labels and milestones

- `ensure-label --name <name> [--color #RRGGBB] [--description <text>]`: looks
  for the name, ignoring case, among the team's labels and workspace labels. An
  active match is returned. Otherwise it creates a team label and reads it
  back. A label group, an archived-only match, an ambiguous match or a
  near-duplicate (same name apart from spacing and punctuation) refuses.
- `ensure-taxonomy`: `ensure-label` for every name in the config's `labels.*`
  lists (`enabled: false` skips it). It checks every name first, so a group,
  an archived-only match or near-duplicate names refuse before the first
  create. `apptrick-set-up` runs it.
- `ensure-milestone --route app --name <name> [--description <text>] [--target-date YYYY-MM-DD]`:
  looks for the exact name in the routed project's milestones, archived ones
  included. A near-duplicate or archived match refuses. Otherwise it creates the
  milestone and reads it back. Playbook phases use one milestone each.

Concurrent runs: each ensure command searches, then creates. Two runs at the
same moment can both find nothing and both create, leaving a duplicate. Later
runs then refuse the name as ambiguous until the owner removes one (deletion
needs the owner's approval). Run set-up and provisioning from one session at a
time. Issue creation has the same property for one title.

## Claim operations

The edition's claim protocol (`claim-pr.md`, "Applying the claim" and
"Release / handback") names tracker operations. For a Linear issue they map to
these adapter commands, and only these:

| Claim protocol operation | Adapter command |
|---|---|
| **current-user** | `list-comments` prints `viewerId` (and `assign-issue` resolves the viewer itself) |
| read the item | `get-issue` (state, labels, assignee) |
| assign | `assign-issue --issue <KEY>-<n> [--force]` |
| `apply_label` / unlabel | `add-label` / `remove-label --issue <KEY>-<n> --label <name>` |
| **list-issue-comments** | `list-comments --issue <KEY>-<n> [--marker <text>]` |
| **update-comment** (marker upsert) | `upsert-comment --issue <KEY>-<n> --body-file <file> [--marker <text>]` |

- `assign-issue` assigns the issue to the credential's own user. The viewer ID
  comes from the API (`viewer { id }`); `auth whoami` is never used. Already
  assigned to the viewer: no write. Assigned to someone else: refused as a
  claim conflict, unless `--force` (the documented takeover). Readback: the
  assignee ID equals the viewer ID.
- `add-label` adds one existing label (`ensure-label` first) and keeps the
  others (`issue update --add-label`); `remove-label` removes one and keeps the
  others (`--remove-label`). A label already present, or already absent, means
  no write. Readback: the label is present, or absent.
- `list-comments` reads every comment page, oldest first, and prints each
  comment's ID, author ID, `mine` (written by the viewer), times and redacted
  body. An incomplete read is `SEARCH_UNAVAILABLE`: the comment history is not
  proved, so the claim stops.
- `upsert-comment` keeps exactly one comment carrying the marker (default
  `` `apptrick-run-ownership` ``, the run-ownership marker). The body file must
  contain the marker. No such comment: `issue comment add`. One comment by the
  viewer with another body: `issue comment update` in place. The same body
  (ignoring line endings, trailing spaces and outer blank lines): no write. A
  marker comment by another user, or two marker comments, refuse. Readback:
  exactly one marker comment, by the viewer, with the new body.

Every claim command writes only to issues in routed projects, never to an
archived issue, and follows the `UNCERTAIN_WRITE` rule above. The claim and
release order is in the apptrick-deliver extension ("Claim and release").

## New app project

`ensure-project --name "<App name>" [--description <text>] [--status planned]`:

1. Read every project in the workspace, archived ones included.
2. An exact name in the bound team is returned unchanged. An exact name in another
   team, an archived match, a near-duplicate (case, spacing, punctuation) or two
   exact matches refuse.
3. Otherwise `project create --team <team> --name ... --status planned --json`,
   then read it back by name.

Then bind it: the template's `scripts/bind_app_project.py --project <uuid> ...`
verifies the project is in the team and writes `linear.project`; set
`linear.routing.app` to the same UUID. Never reuse the template's project for an
app. `ensure-project` never edits an existing project.

## GitHub integration and double moves (D5)

Linear's GitHub integration moves issues on Git events: draft PR (`draft`),
PR open (`start`), review request (`review`), ready to merge (`mergeable`) and
merge (`merge`). Once the integration is installed, an event without a rule
gets Linear's default move (for example In Progress when a PR opens, Done on
merge). With the harness moving states too, a default move would move issues
twice.

The model the harness uses: setting an event to "No action" in Linear's
settings UI stores a default rule (no target branch) whose state is empty, and
`git-automation` reads such a rule as "No action". Deleting a rule restores the
default move. The API cannot write "No action": Linear's API documentation says
a default rule created through the API must have a state. So only the UI step
below can set it, and the tool never changes team settings. This model is not
yet observed live, because no Git integration is installed.

`git-automation` shows whether the workspace has a GitHub or GitLab
integration and whether the team has Git automation rules.

How the harness keeps it that way:

- `git-automation` lists the team's rules and the workspace's Git integrations.
  It fails when any rule (default or target-branch) has a state, and, when a
  Git integration is installed, when any of the five events lacks a default
  rule with an empty state (`defaultMoves` lists them). It also fails when the
  credential is not a workspace admin (`"viewerAdmin": false`), because a
  non-admin may not see every integration. `apptrick-set-up` runs it with
  `auth-check` and `states`.
- PR bodies use `Refs <KEY>-<n>`, never a closing keyword, so a later integration
  cannot close issues from PR text.
- `transition-issue --from` and the history check make an automatic move show
  up as a refusal or a reported conflict, not a silent overwrite.

Manual step for the owner, only if the GitHub integration is installed: in
Linear, Settings > Team > Workflows & automations > Pull request and commit
automations (the bound team), set every event to "No action", also for every
target-branch rule, then run `git-automation` and expect `"ok": true`.

If `git-automation` still fails after that step with only `defaultMoves` left
(Linear did not store "No action" as a rule without a state), the owner records
an approved exception: the date, the full `git-automation` output and the
owner's approval go into the app's `SDLC.md` "Harness deviations" project
lines. Set-up then continues, and the `--from` guard and the history check stay
the only protection against a double move. An active rule with a state is never
an exception; change it in the UI.

## Secrets and logs

- Credentials stay in the CLI's keyring, or in `LINEAR_API_KEY` in the
  environment for CI. The tool never reads, prints or passes a credential, and
  never runs `auth token`.
- An argument that looks like a Linear token (`lin_api_...`, `lin_oauth_...`,
  `Bearer ...`) refuses before the CLI runs.
- Every printed message and command is redacted: tokens become `[REDACTED]`,
  e-mail addresses become `[email]`. `--verbose` prints each redacted command on
  stderr.

## Tests

The tests live in the harness repository only (paths from its root):

- Offline: `tests/test_apptrick_linear.py` runs every command against a fake
  CLI (`tests/fake_linear.py`), including idempotency, refusals, uncertain
  writes, pagination limits and redaction.
- Live, read-only: `APPTRICK_LINEAR_LIVE=read python3 -m unittest tests.test_apptrick_linear_live`
  runs `auth-check`, `states` and `git-automation` against the configured
  team.
- Live, write: `APPTRICK_LINEAR_LIVE=write` also runs the write sequence in the
  throwaway project "Harness adapter test (P3)": project, label, milestone,
  issue and sub-issue (each ensured twice), then every state with readback.
  It never deletes or archives anything; the owner decides about the project.

## Not covered

- Estimates (`UNSUPPORTED_OPERATION`, as in the generic descriptor).
- Issue relations (`linear issue relation`), project updates, comments other
  than marker comments, and close comments stay with the generic descriptor.
- Pull requests, their labels, comments and claims stay with
  `.ai/trackers/github.md`.
