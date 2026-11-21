# Task routing after read-only intake

Run this decision before task creation, claim, run-file persistence, worktree
creation, or any other mutation. Ticket presence alone never chooses the route.

## 1. Existing-run continuation wins

Search read-only evidence using every identity currently available: canonical
provider-native task reference, resolved spec path, stable `RUN_ID`, derived plan
slug, task branch convention, `Tracking plan:` / `Tracking run folder:` PR body
lines, and the stable ownership marker. For a free-form description, use the
issue creator's read-only duplicate search before authorizing create.

- A matching open plain-plan PR resumes through `apptrick-continue-pr` with the
  inherited `RUN_ID`.
- A matching open run-folder PR resumes through `apptrick-continue-pr-loop` with
  the inherited `RUN_ID`.
- A pushed current-format task branch with a committed plain plan and no PR
  resumes, on any host, only when all of these hold; check item 2 before any
  write in item 1:
  1. Re-enter the claim per `references/claim-pr.md`: the stable ownership
     marker names this `RUN_ID` with status `active` or `handoff`, or terminal
     `aborted` written by this same run with no other ownership signal. Allowed
     local run-context statuses are `active`, `handoff` and `aborted`. Update the
     marker to `active` and read it back before any other write.
  2. **search-prs** finds no PR - open, closed or merged - for this branch or
     issue, and no other owner, assignee or `RUN_ID` holds the issue or branch.
     Any such PR or holder stops the resume and is reported.
  3. An issue-less run has no shared marker yet: its local run slot
     (`<paths.runs>/.sessions/<RUN_ID>.json`) and the pushed branch must both
     match this `RUN_ID` and plan.

  Then open the bare draft PR with `Tracking plan:` and `Status: in-progress`,
  claim it and read back the markers as in the skill's step 8 PR-opening
  sequence, and hand off to `apptrick-continue-pr {PR_NUMBER} --run-id "$RUN_ID"`.
- Any other branch/plan/run folder with no PR (legacy format, run folder, or no
  matching `RUN_ID`) has no supported continuation interface. Stop without
  creating a PR or new run, preserve its `RUN_ID` and artifacts, and report that
  a maintainer must inspect and recover it manually.
- A spec-only design PR is input evidence, not the implementation PR. Resolve its
  spec and continue fresh delivery only when no implementation run exists.
- A conflicting active owner blocks unless the user supplied `--force`; force
  follows the marker replacement/readback protocol and never overwrites artifacts.

Incomplete search results, comments, or ownership history block the decision.
Matching account, assignee, or PR author does not prove same-run ownership.

## 2. Classify the requested outcome

Use the description, canonical issue title/body/labels, resolved spec, and project
instructions together. A label is evidence, not authority to contradict the text.

### Bug investigation

Choose bug investigation when the requested outcome is to diagnose or correct
broken, wrong, crashed, failed, or regressed existing behavior. After canonical
task binding, this route runs `apptrick-verify-bug` before a claim or implementation
write and `apptrick-diagnose` before implementation edits. Authorized issue creation
and local run binding may precede confirmation so a free-form bug has the native
reference those tools require. The shared execution plan starts with a regression
test that fails for the confirmed defect and passes after the fix.

### Feature investigation

Choose feature investigation when the request asks for a new capability but its
readiness, intended behavior, or implementation contract still needs validation.
Apply the ticket-level Definition of Ready, then resolve or author the covering
spec. Already built/in-flight work stops with evidence; not-ready tickets stop
with the exact gaps. Before posting a not-ready result, read complete issue
comments through **list-issue-comments** and find both backticked and legacy bare
forms of `` 🤖 `apptrick-deliver` - not ready `` (accept the historical
U+2014 separator when reading). Create it once with **comment-issue**, or rewrite
the existing marker through **update-comment**. The body names each missing
ticket-level item, the evidence used, and the next action; it never duplicates a
comment on rerun. Inspect/read-only intent reports the same result without posting.

### Agreed delivery

Choose agreed delivery when the description, issue, or covering spec already
defines the observable change and no product or defect investigation remains.
An existing ticket does not make a change agreed. A covering spec may establish
agreement when it resolves material decisions and matches the requested scope.

### Ambiguous or mixed intent

When evidence cannot distinguish a defect, a new capability, and an already
agreed change, stop before any mutation and ask for the intended outcome. When
one task mixes a defect and a materially new capability, stop before any mutation
and ask for a split or an explicit combined scope. Never default ambiguous intent
to a mutating bug chain.

Record one routing line in the eventual plan/report:

```text
Route: existing-run continuation | bug investigation | feature investigation | agreed delivery
Evidence: {one sentence naming the decisive task/spec/code evidence}
```

## 3. Mutation boundary

Only after the route is unambiguous may task intake create/reuse the canonical
task, persist the one stable `RUN_ID`, establish a claim, or create repository
artifacts. Recheck inspect/dry-run intent immediately before each write. `--loop`
is ignored until investigation and spec/plan work is complete.
