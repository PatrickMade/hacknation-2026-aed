# Task intake before repository work

Use this procedure only after read-only input resolution, existing-work detection,
and route selection. Before deriving a task branch, creating a worktree, committing,
or implementing, it binds one task to one stable `RUN_ID`.

## 1. Establish the tracker scope and run identity

Load the configured tracker binding. If the tracker prerequisite is missing, run
`apptrick-set-up --stage tracker --inspect` with the already selected
provider/site/project binding. Keep the returned descriptor as an ephemeral
binding when no descriptor file exists. Use `--repair` only for a failed tracker
prerequisite; setup returns control and this caller retries the original read
once. Do not resolve the default branch during this stage.

Preserve an inherited `RUN_ID`; otherwise generate one UUID for the new logical
run. Before an issue-creation mutation, persist the existing local run context
under `<paths.runs>/.sessions/<RUN_ID>.json` with `taskRef: null`, then update
that same record after canonical readback. Inspect/read-only intent stops before
the local context write and every tracker or repository mutation.

Inspect the existing local run context before deciding to create. When its
`taskRef` is present, require any explicit `--issue` to identify the same item,
validate and read back that task, then reuse it. A mismatch or failed read stops;
never create a replacement. Continue to issue creation only when neither the
explicit argument nor the preserved context supplies a task.

## 2. Resolve an explicit issue

When `--issue <ref>` is present, apply the collection's provider-aware
issue-reference validator before any tracker call. Resolve the installed
`apptrick-deliver` skill and its `scripts/validate-issue-reference.mjs`
helper as the absolute `ISSUE_VALIDATOR` path. If that helper or Node.js is
missing, stop before any tracker operation; do not replace validation inline.
Run the helper with the original reference as a quoted argument:

```bash
node "$ISSUE_VALIDATOR" --provider "$TRACKER" --reference "$ISSUE_REF"
```

Append the scope arguments from the selected descriptor: `--host` and
`--repository` for GitHub, `--host` and `--project` for Jira, or `--host`,
`--workspace` and `--project` for Linear. These arguments are required by this
caller even where the helper permits an unscoped native key. A nonzero exit stops
before tracker access. Parse its JSON `issueId`, `markerId` and optional
`sourceUrl`, then perform canonical readback below. Bind the configured host and
GitHub repository, Jira project, or Linear workspace/project as applicable.
Accept only the provider's valid native form or a URL in that configured scope;
preserve the canonical id and source URL. An issue-shaped malformed value,
provider mismatch, project/workspace/repository mismatch, inaccessible item, or
failed read is a hard stop. An explicit `--issue` failure must never fall
through to brief mode or create another issue.

Read the candidate through the selected descriptor's **get-issue** operation and
require the returned provider, native key, project/repository scope, real title,
body/acceptance, and URL to match the validated reference. Bind these as
`TASK_REF`, `TASK_TITLE`, `TASK_BRIEF`, and `TASK_URL`; when no positional brief
was supplied, the canonical title/body becomes the implementation brief. Existing estimates are read-only on this path;
do not reinterpret `--original-estimate` as permission to change an existing
issue.

## 3. Reuse or create when no issue was supplied

Jira and Linear task delivery require a bound issue. A GitHub repository may
retain brief-only delivery only when its committed project policy does not
require an issue; otherwise follow the same create/reuse path. The bug route
always requires a canonical issue because `apptrick-verify-bug` and `apptrick-diagnose`
consume its native reference. For a free-form bug, use the same authorized
duplicate-search/create/readback path even on GitHub. An explicit no-tracker-write
constraint blocks this route before creation; report the missing issue rather
than invoking diagnostics with an empty `TASK_REF`.

For a new Jira task, require an approved original estimate before invoking the
issue creator. If it is absent, stop before creation and repository work; request
the missing value in the handoff. Do not invent a duration. A supplied existing
issue follows section 2 and does not authorize an estimate change. After creation,
read back the original estimate with the issue identity before repository work;
missing or mismatched estimate evidence blocks that phase without another create.

Invoke the existing issue creator with the original brief:

```text
apptrick-create-issue "{brief}" --tracker-only
```

If `apptrick-create-issue` is unavailable, stop and name that missing skill. Do not
replace its duplicate search, creation, estimate, or readback contract inline.

Forward an estimate only when the exact value came from the user or existing
approved task context:

```text
apptrick-create-issue "{brief}" --tracker-only --original-estimate "$APPROVED_ORIGINAL_ESTIMATE"
```

Never infer an estimate, convert story points, or change remaining estimate or
worklogs. `apptrick-create-issue` performs duplicate search before creation through
the selected descriptor. `SEARCH_UNAVAILABLE`, incomplete results, or failed
candidate readback blocks creation; it is not evidence that no task exists. A
credible duplicate is reused only after canonical **get-issue** readback, without
posting an unapproved duplicate comment.

Consume the exact `Issue:` chaining line from `apptrick-create-issue`, validate
it again, and perform canonical readback. A create with failed or mismatched
readback is `MUTATION_OUTCOME_UNKNOWN`: record the uncertainty and stop. Never
replay that write, switch transport, or create a replacement issue.

## 4. Bind repository identity

After readback, update the local run context with `taskRef` and persist
`TASK_REF`, `TASK_TITLE`, and `TASK_URL` in the execution plan or run-folder
handoff and provider-aware PR linkage. Jira/Linear branch names and every commit
use the native key plus the real read-back title as required by the repository.
Only now resolve the configured base branch and derive the task branch.

Derive `TASK_COMMIT_PREFIX` from the repository's commit convention. For
Jira/Linear it contains the complete `TASK_REF` plus the project-required full
`TASK_TITLE`, without replacing the title with a slug. Apply it to every task
commit, including plan, checkpoint, progress, review-fix, and style-fix commits.
GitHub brief-only work keeps the repository's established commit convention.

An engine handoff passes `--issue "$TASK_REF"` and `--run-id "$RUN_ID"`.
Continuation reads the same task from the local run context plus the committed
plan/run folder and PR linkage. It validates readback before later tracker
mutations and never creates a new issue or PR for that recorded task.
