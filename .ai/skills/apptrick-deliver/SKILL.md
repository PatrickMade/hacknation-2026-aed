---
name: apptrick-deliver
description: "Use when delivering one task end to end with apptrick-deliver, to add the Linear state moves, standing merge authority and Flutter delivery rules."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-deliver

Apply the installed apptrick-deliver skill and SDLC.md. Use the same issue/run/PR on continuation. Read covering feature specs as well as the proportional task spec. Routine in-scope spec approval is already granted. Complete the repository gates and stop at a ready PR in Review (see "Independent review"); after the independent review record and the QA gate, apptrick-merge merges under SDLC standing authority when `delivery.mode` is `autonomous` and the merge has no uncovered production effect. Preserve the installed merge checks. Record code outcomes only after integration; keep external/device blocks on the existing issue. Do not create persistent memories.

## Delivery mode and base

Read both from `.ai/agentic.config.json`; never hard-code them.

- `delivery.mode`: `autonomous` (the default, decision D3) lets agents merge
  through the merge gate; `human-gated` stops every run at a merge-ready PR
  and a human merges.
- `baseBranch`: the branch every task branch starts from and every PR
  targets; `auto` is the repository's default branch.

## Project skill catalog

Follow `docs/AGENT-SKILL-CATALOG.md` for exact-source procedure routing. Resolve
required procedures through project-aware `find-skills`; preserve native
invocation restrictions and the complete upstream workflow.

## Linear states

Move the Linear issue explicitly at each stage with
`.ai/scripts/apptrick_linear.py transition-issue` (contract
`.ai/trackers/linear-adapter.md`), which reads the state back (decision D5,
`SDLC.md` "Linear states"): In Progress at the claim, Review when the ready PR
is open, QA while a `needs-qa` PR waits for QA evidence, Done after the merge
readback with the QA gate satisfied. A blocked task keeps its state; record the
blocked reason and the next executable action on the issue.

## Claim and release

This is the one claim contract of the harness. It overrides the edition's step 5,
the step 8 issue release, step 13, apptrick-open-pr step 8 and the claim-pr
reference wherever they differ. Linear issue operations use only these adapter
commands (`.ai/scripts/apptrick_linear.py`), never raw `linear` commands or the
generic `.ai/trackers/linear.md` descriptor. PR operations use
`.ai/trackers/github.md`.

1. **Check.** `get-issue --issue <KEY>-<n>` and `list-comments --issue <KEY>-<n>`
   (`<KEY>` is `linear.team`; the key matches `ticketKeyPattern`).
   Another assignee, `in-progress`, or an ownership comment with `status: active`
   or `handoff` for another `RUN_ID` is a conflict: stop and report it (stale
   recovery and `--force` follow the claim-pr reference). `SEARCH_UNAVAILABLE`
   means the comment history is not proved: stop.
2. **Claim the issue** (step 5): `assign-issue`, `add-label --label in-progress`,
   `upsert-comment --body-file <marker file>` with the
   `` 🤖 `apptrick-run-ownership` - active run `` marker, `RUN_ID`, task, spec,
   `status: active` and the last completed stage, then
   `transition-issue --to inProgress --from backlog,ready`. Each command reads
   its write back; `UNCERTAIN_WRITE` stops without a replay.

| Item | Event | Marker `status` | `in-progress` |
|---|---|---|---|
| Issue | Claimed | `active` | added |
| Issue | PR opened and its claim read back | `released`, naming the PR | removed |
| Issue | Run stops before a PR opens | `aborted` | removed |
| PR | Claimed when it opens | `active` | added |
| PR | Same run continues in another skill | `handoff` | kept |
| PR | Authoring run ends at the ready PR in Review | `completed` | removed |
| PR | Run fails after the PR opened | `aborted` | removed |

The issue marker is `released`, never `completed`, when the claim moves to the
PR (this replaces apptrick-open-pr's `completed`). Update the marker before
removing the label, read both back, and keep the assignee. A failed PR claim
keeps the issue claim `active` and blocks.

## Independent review

This overrides the edition's step 11, which runs `apptrick-review --autofix` in
the authoring session and so contradicts decision D3.

- The authoring session normalizes the PR (body, complete labels, one
  label-rationale comment), marks it ready, moves the issue to Review, releases
  its PR claim as `completed` and reports. It never runs `apptrick-review` on
  its own PR. The report names the next step: `apptrick-review <PR>` in a new
  session.
- An independent session (a different session ID) runs `apptrick-review`
  without `--autofix` and posts the review record (apptrick-review extension).
  Fixes go back to an authoring session through apptrick-continue-pr or
  apptrick-fix-pr; every new head needs a new record.
- QA evidence (step 12) runs after the independent APPROVE moves a `needs-qa`
  issue to QA.

## Order and commits

- Write or extend the covering spec in `.ai/specs/` and the run plan in
  `.ai/runs/` with numbered Progress before the first implementation edit
  (one task record for a small change, see "Small change").
- Commit subjects are Conventional Commits that name that commit's own change,
  without the Linear key or the issue title. The key goes in the PR body
  (`Refs <KEY>-<n>`) and the `Issue:` line. This replaces `TASK_COMMIT_PREFIX`
  (task-intake "Bind repository identity", pr-finalize, review-report): it is
  empty for every task commit in every `apptrick-` skill.
- Before the validation gate in a fresh worktree, prepare it as the
  apptrick-test extension says ("Fresh worktree preparation").

## Small change

One small agreed change (one behavior; no migration, new dependency, external
contract or open product question) takes the short path:

1. One task record, `.ai/specs/<YYYY-MM-DD>-<slug>.md`, with Problem,
   Outcome, Scope, Acceptance, Verification and a numbered Progress list, is
   both the covering spec and the run plan; there is no `.ai/runs/` plan.
2. Implement it and run `validation.commands` once on the stable candidate;
   review reuses that evidence unless an input changes.
3. QA scope: `python3 -B .ai/scripts/rerun_scope.py --tested <merge base> --head HEAD --base <baseBranch>`,
   with the merge base of `baseBranch` and `HEAD`. `same_head` or
   `carry_over` means no app input changed, so the PR is `skip-qa`; otherwise
   it is `needs-qa` with the scenario IDs `scenarios.py required` names.
   Without a scenario catalog the tool exits 2 (`catalog_missing`); then
   `skip-qa` needs a diff that is only docs, tests or CI (SDLC.md "The QA
   gate"), and any other diff is `needs-qa`.
4. One PR, the independent review and the merge gate, as for any change.

A change that outgrows these limits moves to the full path: write the spec
and the run plan before the next edit.

## Under a coordinator

When a coordinator dispatches this task to an owner lane (SDLC.md
"Coordinator lanes"):

- Invoke every skill (Skill tool, or `$<skill>` on
  Codex). Reading a skill file is not invoking it.
- The owner lane holds no devices: it never runs apptrick-prepare-test-env,
  apptrick-verify, `maestro-cli` or Appium, and sets no QA label. Device QA
  belongs to the QA lane.
- Write this issue's Linear state and description yourself with read-back;
  only new issues go to the tracker scribe. Merge `baseBranch` into the PR
  only for a conflict GitHub shows, a dependency on a newly merged PR, or the
  one update right before the merge (SDLC.md "Coordinator lanes"). Add or
  update the PR's rows in the QA queue file, then report
  `EVENT: READY-QA PR #<n> head <sha8>`. A new head on a PR under QA: set its
  rows to the new head and back to `queued`; QA evidence carries over only
  under the carry rule in SDLC.md "Coordinator lanes" (the project sets
  `qa.carryMode: "strict"` on its base branch).
- For a UI change, start the independent design review of the same head after
  QA's visual review.
- Merge with `apptrick-advance-pr --allow-merge` through the merge gate when
  every gate is green on the head and the merge-order file allows it, then
  report `MERGED`. Otherwise report only `BLOCKED` / `DECISION`.

## Platforms and evidence

- Every product change targets iOS and Android; `iphone_only` limits only the
  iOS form factor. A native-impacting change (`lib/`, `ios/`, `android/`,
  `pubspec.yaml`, `pubspec.lock`, `assets/`, `.maestro/`, `integration_test/`)
  names both platforms and the feature-ledger IDs it touches.
- Source checks (`validation.commands`) prove source behavior only. A PR body
  never claims installed-app behavior from them.
- Device QA follows the apptrick-prepare-test-env and apptrick-verify
  extensions. Release acceptance is a separate run on the project's release
  route.

## Clean repository

Delivery removes what the change supersedes: old code, files, tests, docs and
configuration go in the same change.
<!-- apptrick-harness:end -->
