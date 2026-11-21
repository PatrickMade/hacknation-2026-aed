# Tracker provider: Jira Cloud issues + GitHub pull requests

This is the split-provider implementation of the tracker operations contract for teams that keep issues in Jira Cloud and source code on GitHub. Issue operations use one explicitly selected transport for the whole stage or mutation batch: Atlassian CLI (`acli`) or an available Atlassian Jira MCP integration. Repository, pull-request, review, CI, and PR-label operations delegate to the companion `.ai/trackers/github.md` descriptor only when that later stage is requested.

At runtime, `apptrick-set-up` installs both files and sets `"tracker": "jira"`. The repository's copies are authoritative: teams may add fields, Jira workflow mappings, or project conventions without editing installed skills.

## Prerequisites

- Select `JIRA_TRANSPORT=acli|mcp` from the stage argument, the repository's configured tracker transport, or the old-descriptor default (`acli`), in that order. Bind it once before the first operation and record it in the run context. Never fall through to the other transport after a mutation with an uncertain response; read back through the selected transport and stop with `MUTATION_OUTCOME_UNKNOWN` if certainty cannot be recovered.
- For `acli`, install Atlassian CLI through `apptrick-set-up`, which owns the permission, official per-OS installation, compatibility, and verification flow. Then authenticate with `acli jira auth login --web` or pipe an API token to `acli jira auth login --site <site> --email <email> --token`. Never put a token on the command line or in this descriptor.
- For MCP, select an authenticated Atlassian Jira tool provider and bind the concrete tool namespace for the stage. The operation mappings below name stable tool suffixes so the descriptor remains portable across clients. Tool discovery plus a visible-project read or bounded JQL query proves scoped project access; create/intake does not require an existing issue key. Tool visibility alone does not prove access.
- Set `ATLASSIAN_SITE` to the Jira Cloud hostname (for example, `example.atlassian.net`), `ATLASSIAN_PROJECT` to the default project key, and `ATLASSIAN_ACCOUNT_ID` to the automation user's non-secret Jira account id. For `acli`, also bind `ATLASSIAN_EMAIL` locally to the intended CLI account so auth status can be compared with the authorized target. Do not print either identity value in reports or shared logs.
- Optionally set `ATLASSIAN_ISSUE_TYPE` (default `Task`), `ATLASSIAN_DONE_STATUS` (default `Done`), and `ATLASSIAN_CANCELED_STATUS` (default `Canceled`) to match the project's workflow.
- Install and authenticate the `gh` CLI, and keep the companion `.ai/trackers/github.md` descriptor only before a repository, PR, CI, label, or publication stage. Jira-only intake, read-back, transition, estimate, comment, and issue-management stages do not require either.
- The `acli` transport requires Atlassian CLI 1.3.5-stable or newer because marker-idempotent comments use the comment list/update commands added in the 1.3.4/1.3.5 releases. MCP transport does not require `acli`.
- Atlassian Government Cloud is not supported by the `acli` transport as documented in the official introduction.

## Conventions

- Jira work-item identifiers are project keys plus numbers, such as `ENG-123`. Preserve the native key end to end. A task branch uses the key plus the project-required title slug, and every task commit uses the key plus the project-required task title; resolve that convention from repository instructions or config instead of inventing a global prefix. GitHub does not auto-close Jira issues from `Closes ENG-123`; use `Refs ENG-123` in PR prose and explicitly run **close-issue** only after all required repository outcomes pass.
- `{repo}` means a Jira project key for issue creation/search and `owner/name` for delegated GitHub operations. When omitted, issue commands use `ATLASSIAN_PROJECT`; GitHub commands infer the repository from the checkout.
- Jira has no pull-request object in `acli`. Drafts, reviews, mergeability, CI status, and PR labels are GitHub concepts and always delegate to `.ai/trackers/github.md`.
- The issue claim signals are: assignee account id = `ATLASSIAN_ACCOUNT_ID`, the free-form `in-progress` issue label, and one marker-idempotent ownership comment containing only the opaque run id, task key, repository identifier, covering spec, status, and last completed stage. Local paths, host names, and user identity stay in the local run context. **get-issue** requests assignee, labels, status, and complete comments so all three signals are readable. Matching account identity is never matching run ownership.
- Jira comment ids are only unique with their work item in the CLI. This descriptor serializes them as opaque `{issueKey}:{numericCommentId}` handles (for example, `ENG-123:10042`) from **list-issue-comments** and accepts that handle in **get-issue-comment** and **update-comment**.
- Use file flags for multi-line text: `--description-file` for descriptions and `--body-file` for comments. Mutating bulk-capable commands always pass a single `--key` and `--yes` so an autonomous run neither expands scope through JQL nor waits for confirmation.
- Every create, material field edit, estimate change, transition, assignment, label change, and milestone update is read back before the caller reports success. A denied or incomplete search is `SEARCH_UNAVAILABLE`, never an empty duplicate set.
- Before every issue mutation batch, run **auth-check** and preflight the complete required operation set for the selected transport. A missing operation stops before the first create, claim, comment, label, status, or estimate write. Never switch site, account, or transport automatically.

## MCP operation mapping

Bind these suffixes to the selected authenticated Jira MCP provider. A missing required suffix is an unsupported operation and blocks before writes. Do not guess a similar tool name and do not switch transports mid-batch.

| Provider operation | Required Jira MCP suffix and mapping |
|---|---|
| **auth-check** | Bound tool discovery plus a visible-project read or safe bounded JQL read proving the configured project is accessible |
| **current-user** | Read the configured `ATLASSIAN_ACCOUNT_ID`; no MCP mutation or identity guess |
| **get-issue** | `getjiraissue`: `cloudId`, `issueIdOrKey`, requested `fields`, optional `expand`; use `expand: "editmeta"` to discover whether `timetracking` is editable |
| **search-issues** | `searchjiraissuesusingjql`: `cloudId`, escaped `jql`, `fields`, `maxResults`, and `nextPageToken` until complete |
| **create-issue** | `createjiraissue`: `cloudId`, `projectKey`, `issueTypeName`, `summary`, optional `description`/`assignee_account_id`, and supported `additional_fields`; then **get-issue** |
| **update-issue**, assign/unassign, label/unlabel | `editjiraissue`: `cloudId`, `issueIdOrKey`, and a `fields` object containing only intended fields; then **get-issue** |
| **comment-issue** | `addcommenttojiraissue`: `cloudId`, `issueIdOrKey`, and `commentBody`; then read comments back |
| **update-comment** | `addcommenttojiraissue`: `cloudId`, `issueIdOrKey`, `commentBody`, and existing `commentId`; then read that comment back |
| **list-issue-comments**, **get-issue-comment** | `getjiraissue` requesting comments, only when its response proves complete comment pagination; otherwise `UNSUPPORTED_OPERATION` before claim, duplicate, or marker decisions |
| **discover-issue-transitions** | `gettransitionsforjiraissue`: `cloudId` and `issueIdOrKey` |
| **transition-issue** | `transitionjiraissue`: `cloudId`, `issueIdOrKey`, and `transition: { id }`; then **get-issue** |
| **get-issue-estimate** | `getjiraissue` with `fields: ["timetracking"]` |
| **set-issue-original-estimate** | `editjiraissue` with only `fields.timetracking.originalEstimate`; then read back `originalEstimateSeconds` and require `remainingEstimateSeconds` unchanged |
| **verify-issue-outcomes** | Reconcile the explicit `requiredRepositories` array through companion GitHub read operations; no Jira mutation |
| **upsert-issue-milestone** | Complete comment read plus `addcommenttojiraissue` create/update mapping above; fail closed when complete history cannot be proved |
| **close-issue** | **verify-issue-outcomes**, **comment-issue**, **discover-issue-transitions**, and **transition-issue** composition; then **get-issue** status readback |

The MCP issue payload may contain only a truncated comment page. Use the comment operation's complete pagination when available. If completeness cannot be proved, claim, ownership, marker-idempotency, and duplicate decisions fail closed rather than treating unseen comments as absent.

## Label guards

Jira's standard Labels field contains free-form values; there is no separately provisioned label registry to query. In Jira terms, existence means a non-empty syntactically valid value. The guard still honors `labels.enabled: false`, merges instead of replacing existing labels, and reads the result back.

```bash
jira_issue_label_exists() {
  [ -n "$1" ] && ! printf '%s' "$1" | grep -q '[[:space:],]'
}

apply_issue_label() {
  if [ "$LABELS_ENABLED" != "true" ]; then return 0; fi
  if jira_issue_label_exists "$1"; then
    labels=$(acli jira workitem view "$2" --fields labels --json \
      | jq -r --arg label "$1" '((.fields.labels // .labels // []) + [$label]) | unique | join(",")')
    acli jira workitem edit --key "$2" --labels "$labels" --yes
    acli jira workitem view "$2" --fields labels --json \
      | jq -e --arg label "$1" '(.fields.labels // .labels // []) | index($label)' >/dev/null
  else
    echo "Skipping Jira label '$1' (labels must be non-empty and contain no spaces or commas)."
  fi
}

remove_issue_label() {
  if [ "$LABELS_ENABLED" != "true" ]; then return 0; fi
  if jira_issue_label_exists "$1"; then
    acli jira workitem edit --key "$2" --remove-labels "$1" --yes
  fi
}
```

PR label helpers (`label_exists`, `apply_label`, `remove_label`, and `set_pipeline_label`) execute exactly as defined in `.ai/trackers/github.md`. Setup's **list-labels** and **ensure-label-taxonomy** operations provision the GitHub PR taxonomy. Jira issue labels need no creation step; issue-authoring skills may apply the same category, priority, risk, `in-progress`, and `do-not-close` values directly through the guard.

## Operations

### Identity and repository

#### auth-check

Verify only the selected stage and required operation set. Jira-only work must not probe GitHub:

If `acli` is missing or incompatible, run `apptrick-set-up` to provision or repair it. Incompatible means the version is below the documented floor or any required capability probe below fails. That skill asks for installation permission or honors approval already granted in the current session; this descriptor never installs a system CLI itself. If setup cannot obtain permission in an unattended run, surface its `⚠️ NEEDS HUMAN CONFIRMATION` result and stop. After setup succeeds and returns, the original caller retries the tracker operation once from its beginning. Do not loop between the operation and setup.

```bash
atlassian_tracker_auth_check() {
  [ "${JIRA_TRANSPORT:-acli}" = "acli" ] || {
    echo "MCP auth-check must execute the bound provider's visible-project read or safe bounded JQL read for ATLASSIAN_PROJECT; a shell echo is not a capability probe." >&2
    return 2
  }
  command -v acli >/dev/null || {
    echo "Atlassian CLI is not installed; run apptrick-set-up to provision it: https://developer.atlassian.com/cloud/acli/guides/install-acli/" >&2
    return 1
  }
  acli_status=$(acli jira auth status 2>&1) || {
    echo "Atlassian CLI is not authenticated; run acli jira auth login --web, then retry." >&2
    return 1
  }
  : "${ATLASSIAN_SITE:?Set ATLASSIAN_SITE to the Jira Cloud hostname}"
  : "${ATLASSIAN_PROJECT:?Set ATLASSIAN_PROJECT to the default Jira project key}"
  : "${ATLASSIAN_ACCOUNT_ID:?Set ATLASSIAN_ACCOUNT_ID to the Jira account id for the automation user}"
  : "${ATLASSIAN_EMAIL:?Set ATLASSIAN_EMAIL locally to the intended acli account}"
  printf '%s' "$ATLASSIAN_SITE" | grep -Eq '^[A-Za-z0-9.-]+$' || {
    echo "ATLASSIAN_SITE must be a hostname without a scheme or path" >&2
    return 1
  }
  active_site=$(printf '%s\n' "$acli_status" | sed -n 's/^[[:space:]]*Site:[[:space:]]*//p' | head -n 1)
  active_email=$(printf '%s\n' "$acli_status" | sed -n 's/^[[:space:]]*Email:[[:space:]]*//p' | head -n 1)
  active_site=${active_site#https://}
  active_site=${active_site%/}
  if [ -z "$active_site" ] || [ -z "$active_email" ] || [ "$active_site" != "$ATLASSIAN_SITE" ] || [ "$active_email" != "$ATLASSIAN_EMAIL" ]; then
    echo "The active Jira CLI target does not match the authorized site or account; stop before writes and select the intended local session explicitly." >&2
    return 1
  fi
  acli jira workitem edit --help | grep -Fq -- '--remove-labels' &&
    acli jira workitem comment list --help | grep -Fq -- '--paginate' &&
    acli jira workitem comment update --help | grep -Fq -- '--body-file' || {
    echo "Installed acli is incompatible with the required 1.3.5-stable+ command surface; run apptrick-set-up to repair it." >&2
    return 1
  }
  if [ "${REQUIRES_CODE_HOST:-false}" = "true" ]; then
    [ -f .ai/trackers/github.md ] || {
      echo "Missing companion .ai/trackers/github.md" >&2
      return 1
    }
    gh auth status
  fi
}
atlassian_tracker_auth_check
```

Do not print `acli_status`, the parsed email, or the configured account id. Before a mutation batch, the caller also declares its required issue operations. With `acli`, any batch requiring **discover-issue-transitions**, **transition-issue**, or **set-issue-original-estimate** returns `UNSUPPORTED_OPERATION` before its first write. The CLI exposes `workitem transition --status`, but its current surface does not expose the discovery operation required to select and prove a valid transition. Read-only **get-issue-estimate** remains supported through `workitem view`.

#### current-user

For an issue claim, use the configured Jira account id for assignment comparison and the run id from the ownership marker for ownership comparison. For a PR claim, execute **current-user** from `.ai/trackers/github.md` only in a PR stage.

```bash
CURRENT_USER=${ATLASSIAN_ACCOUNT_ID:?Set ATLASSIAN_ACCOUNT_ID}
```

#### repo-info

Repository identity comes from **repo-info** in `.ai/trackers/github.md`. Jira issue scope is `${ATLASSIAN_SITE}/${ATLASSIAN_PROJECT}` (or the explicit project key passed as `{repo}`); never silently substitute a GitHub repository name for a Jira project key.

#### default-branch

Execute **default-branch** from `.ai/trackers/github.md`.

### Issues

#### get-issue

`{issueId}` and requested fields -> structured issue data. Validate the native key as `^[A-Z][A-Z0-9_]{1,31}-[1-9][0-9]*$`. Request only the fields the caller names; the full claim/review field set is:

```bash
acli jira workitem view "{issueId}" \
  --fields key,issuetype,summary,status,reporter,assignee,description,labels,priority,created,updated,comment \
  --json
```

Construct the browser URL as `https://${ATLASSIAN_SITE}/browse/{issueId}` when the JSON does not include one.

#### search-issues

Text query, state, optional project → matching work items. Escape backslashes and double quotes before placing user text in JQL; never interpolate raw query text.

```bash
jql_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

escaped_query=$(jql_escape "<query>")
project_key=${JIRA_PROJECT_OVERRIDE:-$ATLASSIAN_PROJECT}
case "$project_key" in
  ''|*[!A-Za-z0-9_-]*) echo "Invalid Jira project key: $project_key" >&2; exit 1 ;;
esac

# open
acli jira workitem search \
  --jql "project = \"${project_key}\" AND statusCategory != Done AND text ~ \"${escaped_query}\"" \
  --paginate --json

# closed
acli jira workitem search \
  --jql "project = \"${project_key}\" AND statusCategory = Done AND text ~ \"${escaped_query}\"" \
  --paginate --json
```

For any state, omit the `statusCategory` clause. Set `JIRA_PROJECT_OVERRIDE` from `{repo}` only after validating it as a Jira project key.

#### create-issue

Title, description body file, assignee, labels, and optional project → created issue JSON. Join guarded labels with commas for the repeatable `--label` input.

```bash
acli jira workitem create --project "${JIRA_PROJECT_OVERRIDE:-$ATLASSIAN_PROJECT}" \
  --type "${ATLASSIAN_ISSUE_TYPE:-Task}" --summary "<title>" \
  --description-file <body-file> --assignee "${ASSIGNEE:-$ATLASSIAN_ACCOUNT_ID}" \
  <optional: --label "<comma-separated-labels>"> --json
```

Read the returned key, re-run **auth-check** if the CLI session may have changed, then call **get-issue** for `key,project,summary,status,assignee,labels,created,updated`. Bind the result to the freshly verified auth site/account plus requested project, native key, and title. Do not compare the JSON `self` URL hostname with `ATLASSIAN_SITE`; Jira may return an internal REST host. Report `https://${ATLASSIAN_SITE}/browse/<key>` only after those checks. An inaccessible or mismatched read-back is not a successful create result.

#### close-issue

First preflight **verify-issue-outcomes**, **comment-issue**, **discover-issue-transitions**, and **transition-issue**. Because current `acli` lacks transition discovery, its close flow returns `UNSUPPORTED_OPERATION: discover-issue-transitions` before posting the closing comment or changing status. With MCP, verify the complete repository inventory, post the closing explanation/PR links, discover the available transitions, select the configured Done/Canceled transition by returned id, invoke **transition-issue** once, and read status back. Use `ATLASSIAN_CANCELED_STATUS` only when the caller's reason is explicitly not-planned; otherwise use `ATLASSIAN_DONE_STATUS`.

Do not substitute `acli jira workitem transition --status` for the missing discovery capability.

#### comment-issue

```bash
acli jira workitem comment create --key "{issueId}" --body-file <body-file> --json
```

#### update-issue

Pass only the fields that changed; `--yes` prevents a confirmation prompt. Read each changed field back before success.

```bash
acli jira workitem edit --key "{issueId}" --summary "<new-title>" --yes --json
acli jira workitem edit --key "{issueId}" --description-file <body-file> --yes --json
```

#### assign-issue / unassign-issue

```bash
acli jira workitem assign --key "{issueId}" --assignee "<email-or-account-id-or-@me>" --yes --json
acli jira workitem assign --key "{issueId}" --remove-assignee --yes --json
```

#### label-issue / unlabel-issue

Always use `apply_issue_label "<label>" "{issueId}"` / `remove_issue_label "<label>" "{issueId}"` from the guard above.

#### get-issue-comment

Parse the opaque `{issueKey}:{commentId}` handle, list that issue's comments, and select the requested id:

```bash
printf '%s' "$COMMENT_HANDLE" | grep -Eq '^[A-Z][A-Z0-9_]+-[0-9]+:[0-9]+$' || {
  echo "Invalid Jira comment handle: $COMMENT_HANDLE" >&2
  exit 1
}
issue_key=${COMMENT_HANDLE%%:*}
comment_id=${COMMENT_HANDLE#*:}
acli jira workitem comment list --key "$issue_key" --paginate --json \
  | jq --arg id "$comment_id" --arg key "$issue_key" --arg site "$ATLASSIAN_SITE" '
      (.comments // .values // .)[]
      | select((.id | tostring) == $id)
      | {id: ($key + ":" + (.id | tostring)), body, author, created, updated,
         url: ("https://" + $site + "/browse/" + $key + "?focusedCommentId=" + (.id | tostring))}'
```

#### list-issue-comments

Return normalized comments whose `id` is the composite handle consumed by the two comment-id operations:

```bash
acli jira workitem comment list --key "{issueId}" --paginate --json \
  | jq --arg key "{issueId}" --arg site "$ATLASSIAN_SITE" '
      [(.comments // .values // .)[]
       | {id: ($key + ":" + (.id | tostring)), body, author, created, updated,
          url: ("https://" + $site + "/browse/" + $key + "?focusedCommentId=" + (.id | tostring))}]'
```

#### update-comment

```bash
printf '%s' "$COMMENT_HANDLE" | grep -Eq '^[A-Z][A-Z0-9_]+-[0-9]+:[0-9]+$' || {
  echo "Invalid Jira comment handle: $COMMENT_HANDLE" >&2
  exit 1
}
issue_key=${COMMENT_HANDLE%%:*}
comment_id=${COMMENT_HANDLE#*:}
acli jira workitem comment update --key "$issue_key" --id "$comment_id" --body-file <body-file>
```

Read the updated comment back. In MCP mode call `addcommenttojiraissue` with the existing `commentId`, then read that comment back.

#### discover-issue-transitions

For `acli`, return `UNSUPPORTED_OPERATION: discover-issue-transitions`; its current transition command supports `--status` mutation but exposes no list/discovery surface. For MCP, call `gettransitionsforjiraissue` with `cloudId` and `issueIdOrKey`, retain stable id and display name, and stop before mutation if the configured destination is absent.

#### transition-issue

Use only a transition returned by **discover-issue-transitions** for the same issue and current status. With MCP, call `transitionjiraissue` using `cloudId`, `issueIdOrKey`, and `transition: { id }`. With `acli`, return `UNSUPPORTED_OPERATION: transition-issue` before mutation because the required discovery proof is unavailable. Invoke MCP once, then call **get-issue** for `key,status`. A missing read-back or unexpected status is `MUTATION_OUTCOME_UNKNOWN`; never replay through the other transport.

#### get-issue-estimate / set-issue-original-estimate

For **get-issue-estimate**, with MCP call `getjiraissue` with `fields: ["timetracking"]`. With `acli`, call `acli jira workitem view "{issueId}" --fields timetracking --json`. Return the estimation scheme plus `originalEstimateSeconds`, `remainingEstimateSeconds`, and worklog total when present. This is a read capability and does not imply that `acli` can edit the estimate.

For **set-issue-original-estimate**, MCP is required. Read **get-issue-estimate** first, call `editjiraissue` with only `fields.timetracking.originalEstimate` set to the approved Jira duration, then read it again. Require the intended `originalEstimateSeconds` and require `remainingEstimateSeconds` and worklogs to equal their pre-write values. Never translate story points into time. A project that uses another estimation scheme must map its editable field explicitly in its committed descriptor before any write. `acli` reports `UNSUPPORTED_OPERATION: set-issue-original-estimate` before mutation; do not improvise a raw REST or JSON flag.

#### verify-issue-outcomes

Read the issue's required repository inventory from its accepted scope/spec or a marker-idempotent implementation milestone. For every named repository, record repository identity, required branch, PR or revision, outcome (`accepted`, `blocked`, or `missing`), and evidence link. Use the companion descriptor's read operations only for repository outcomes in scope. Return accepted only when every expected repository appears exactly once and is accepted. Missing, duplicate, inaccessible, or merely open outcomes block **close-issue**.

#### upsert-issue-milestone

Milestones are concise English records for meaningful `start`, `blocker`, `implementation`, `verification`, `pr`, or `deployment` changes. Find the stable marker `` 🤖 `{skill-name}` - {kind} `` (milestones written before 2026-09-11 use an em dash, U+2014, as that separator; match both) through the complete **list-issue-comments** result, update it through **update-comment**, or create it once through **comment-issue**. Name the actual result, evidence, blocker, and next action; omit empty sections. Routine heartbeats and per-step narration stay in local run records.

Ownership uses one separate marker `` 🤖 `apptrick-run-ownership` - active run ``. Its body contains only opaque run id, task key, repository identifier, covering spec, status, and last completed stage. Update the same record on hand-off, completion, or abort. Preserve and parse legacy `🤖` claim/take-over/hand-off comments; never delete them before the new ownership marker exists. If the selected descriptor cannot update comments, post at most one replacement that states which legacy record it supersedes, then stop adding stage hand-off comments.

### Pull requests

Every operation in this section executes the same-named operation from `.ai/trackers/github.md`, preserving its inputs, outputs, guards, pagination, and cross-repository rules.

#### get-pr
Delegate to GitHub **get-pr**.

#### list-prs
Delegate to GitHub **list-prs**.

#### search-prs
Delegate to GitHub **search-prs**. Search for a Jira key such as `ENG-123` as plain text rather than a GitHub `#123` reference.

#### create-pr
Delegate to GitHub **create-pr**. Reference the Jira key in the body, then use **comment-issue** to attach the resulting PR URL to Jira.

#### update-pr
Delegate to GitHub **update-pr**.

#### comment-pr
Delegate to GitHub **comment-pr**.

#### attach-image-evidence
Delegate to GitHub **attach-image-evidence**.

#### assign-pr / unassign-pr
Delegate both operations to GitHub.

#### label-pr / unlabel-pr
Delegate both operations and all PR label guards to GitHub.

#### get-pr-diff
Delegate to GitHub **get-pr-diff**.

#### get-pr-files
Delegate to GitHub **get-pr-files**.

#### checkout-pr
Delegate to GitHub **checkout-pr**.

#### review-pr
Delegate to GitHub **review-pr**.

#### merge-pr
Delegate to GitHub **merge-pr**. After a successful merge, call Jira **close-issue** explicitly.

#### mark-pr-ready
Delegate to GitHub **mark-pr-ready**.

#### get-pr-checks
Delegate to GitHub **get-pr-checks**.

#### get-required-checks
Delegate to GitHub **get-required-checks**.

#### get-pr-comment / get-review-comment
Delegate both operations to GitHub.

#### list-review-comments
Delegate to GitHub **list-review-comments**.

### CI runs

#### list-runs
Delegate to GitHub **list-runs**.

#### get-run
Delegate to GitHub **get-run**.

#### get-run-failed-logs
Delegate to GitHub **get-run-failed-logs**.

#### rerun-failed
Delegate to GitHub **rerun-failed**.

#### watch-run
Delegate to GitHub **watch-run**.

### Labels

#### list-labels
Delegate to GitHub **list-labels**; this is the PR label taxonomy setup inspects.

#### create-label
Delegate to GitHub **create-label**.

#### ensure-label-taxonomy
Delegate to GitHub **ensure-label-taxonomy**. Jira issue labels are free-form and need no provisioning step.
