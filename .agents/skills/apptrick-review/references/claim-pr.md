# Claiming and releasing work - issues and PRs

The generalized claim/lock procedure for any tracker item (issue or PR) an autonomous run takes ownership of. All reads and mutations go through the tracker descriptor's operations; label mutations only through the `apply_label` guard.

## Run context and ownership

Create one stable `RUN_ID` for the logical run or resume an explicitly handed-off id. Persist `<paths.runs>/.sessions/<RUN_ID>.json` before a write with only: `runId`, provider-native `taskRef`, repository identifier, local `worktree`, `specPath`, `completedStages`, `lastCompletedStage`, `status`, and `requiredRepositories`. The last field is an array of `{ repository, requiredBranch, pullRequest, revision, outcome, evidence }`, one entry per accepted repository in scope; `outcome` is `pending`, `accepted`, or `blocked`. Run `status` is `active`, `handoff`, `completed`, `aborted`, or `released`. Paths and host/user identity stay local. Inspect/dry-run mode exits before creating this file or any tracker/repository mutation.

Cross-host ownership comes from one marker-idempotent comment, `` 🤖 `apptrick-run-ownership` - active run ``, containing only `RUN_ID`, task ref, repository identifier, covering spec, status, and last completed stage. Read it completely before claiming and re-read it after the claim update. Matching account/assignee or PR authorship is context, never authorization or run ownership. Without provider compare-and-swap this detects collisions but is not an atomic distributed lock. A legacy claim without `RUN_ID` has unknown ownership: continue only after an explicit handoff, documented stale recovery, or `--force`; never treat the same account as permission. Update this one marker across chain stages instead of posting hand-off heartbeat comments. Parse legacy claim/take-over/hand-off markers for compatibility and leave them intact.

## Three-signal in-progress check

Resolve `CURRENT_USER` via the tracker operation **current-user**, then read the item (for PRs via **get-pr**; for issues via the descriptor's issue-read operation). The item counts as **already in progress** when ANY of these signals holds:

1. **Assignee** - another assignee is a conflict signal; the same assignee is not proof of matching run ownership.
2. **`in-progress` label** - the label is present on the item.
3. **Ownership comment** - a fresh stable ownership marker with `status: active` or `status: handoff` names a different `RUN_ID`, or complete comment history cannot be proved. A terminal `completed`, `aborted`, or `released` marker is history, not an active claim.

Decision:

- No signal → claim and proceed.
- The ownership marker names this `RUN_ID` and the local run context matches → explicit re-entry; update the marker and continue.
- Signals point at someone else → **STOP** and report the owner - unless the lock is stale (below) or `--force` was passed.

**`ci-monitoring` is not a lock signal.** It is a meta label meaning the previous run's work is *finished and fully reported* - labels applied, review submitted, comments posted - and that run is only watching CI, so it still owes a CI-result follow-up comment. An item carrying `ci-monitoring` **and none of the three signals above** is **not** in progress: claim it and proceed normally, without `--force` and without an override comment. Never fold `ci-monitoring` into the three-signal check, and never treat it as a reason to back off; the whole point of the label is that a monitoring process which dies leaves an honest state rather than a lock nobody holds. When `in-progress` and `ci-monitoring` are both present, the `in-progress` signal decides - `ci-monitoring` neither adds to it nor cancels it.

## Stale-lock recovery

A claim is **stale** when the newest claim signal is older than the applicable stale window and the claimant has produced no commits, comments, or label changes on the item since. Record the stale-ownership evidence in the local run report, then replace and re-read the stable ownership marker with the authorized `RUN_ID` before work. Do not post a separate takeover heartbeat or silently overwrite a live claim.

## `--force` override

`--force` bypasses the conflict stop, never the transparency: document the previous owner and reason in the local run report, then replace and re-read the stable ownership marker with the authorized `RUN_ID`. Do not post a separate override heartbeat.

## Applying the claim

Idempotent - safe to re-run on re-entry:

1. Assign `CURRENT_USER` to the item via the descriptor's assign operation.
2. Apply the `in-progress` label via the `apply_label` guard (missing label → logged skip; `labels.enabled: false` → skip and note it in the report).
3. Upsert the stable ownership marker with this `RUN_ID`, `status: active`, task/spec/repository, and current stage, then read it back. Do not create another claim heartbeat.

## Release / handback

When the run finishes, hands off, or aborts:

- Update the local context and stable ownership marker first: `handoff` while the same run continues in another skill; otherwise the terminal `completed`, `aborted`, or `released` outcome. Include the last completed stage, upsert the same marker through **update-comment**, and read it back. A terminal marker never remains `active`, including when labels are disabled.
- Remove the `in-progress` label via the guard - and when the run intends to follow up with CI results after reporting, **swap** rather than simply remove: `apply_label "ci-monitoring"` in the same breath, so the item is never observably unlabeled and the outstanding follow-up is visible. Remove `ci-monitoring` when the CI-result comment is finally posted, or when the CI wait is abandoned at its `ci.maxWaitMinutes` cap (nobody is monitoring then, and leaving the label would promise a follow-up that never comes). A run that does no CI follow-up at all just removes `in-progress` as before and never applies `ci-monitoring`.
- Post a short release comment stating the outcome.
- The claimant releases their own claim - never release a lock another agent holds.

## Chained hand-off - a live chain never drops its lock

When the same run (same `RUN_ID`) finishes one skill and continues on the same item with another - `apptrick-open-pr` → `apptrick-review`, review → UI QA, or any flow-runner chain - the lock is **transferred, never released and re-acquired**. A release-then-reclaim seam leaves the item observably unclaimed mid-run: any concurrent actor's three-signal check reads "not in progress" and legitimately starts duplicate work, and humans watching the tracker see no owner and no state.

- **Hand-off (finishing step):** keep the `in-progress` label and lock assignee in place; update the stable ownership marker with the next phase and last completed stage. Post no hand-off heartbeat comment:

  Legacy consumers may still parse this prior hand-off marker, but new runs do not emit it.

- **Take-over (next step):** re-read the stable ownership marker and require this `RUN_ID`; before any other work, update its stage and local run context.

  Legacy consumers may still parse this prior take-over marker, but new runs do not emit it.

- **Ownership:** a skill releases only a lock its own run opened. An inherited (handed-off) lock is annotated in the completion comment (`Lock retained - chain continues.`) and released by the chain's driving skill at the end of the run, or by its failure path - "the claimant releases their own claim" applies to the chain as a whole.
- **Crash recovery (adoption):** unknown or legacy ownership is never same-run re-entry. A standalone run may adopt only after the documented stale window and activity checks, or through an explicit handoff/`--force`; update the stable ownership marker before work and own its final release. Preserve other worktrees, processes, and browser sessions.
- **Invariant:** an item under active automation is never observably unclaimed: the stable marker update precedes work, and its handoff or terminal update is the stage's last ownership mutation.

## apptrick-review specifics

This skill claims the PR itself (step 1 of the skill body) and uses tighter windows than the generic defaults.

**Detection.** Preserve the inherited/resumed `RUN_ID`, run **current-user** only for account context, then **get-pr** for `{prNumber}` requesting `assignees`, `labels`, `number`, `title`, and complete `comments`. Active ownership comes from a nonterminal stable marker and its `RUN_ID`; assignee/account signals cannot authorize re-entry. Incomplete history blocks.

Decision tree:

| State | `--force` set? | Action |
|-------|---------------|--------|
| Not in progress | - | Claim and proceed |
| In progress, the same `RUN_ID` owns the lock | - | Re-entry (including a chain handoff from `apptrick-open-pr --handoff` or a flow runner's outer claim): update and re-read the stable marker for the review stage **before any review work**, then proceed without a new claim |
| In progress, someone else owns the lock | no | **STOP**. Ask the user: "PR #{prNumber} is in progress (owner: {owner}, signal: {label/assignee/comment}). Override and continue?" Only continue when the user explicitly says yes. |
| In progress, someone else owns the lock | yes | Record the authorized override locally, replace and re-read the stable marker, then proceed |

**Stale lock**: if the `in-progress` label is older than **60 minutes** and the assignee did not push or comment in that window, treat it as expired. Still ask the user before overriding unless `--force` was set.

**Claim** (only after the check passes) - three tracker operations:

1. **assign-pr**: add `$CURRENT_USER` as an assignee signal on `{prNumber}`.
2. Run `apply_label "in-progress" {prNumber}`.
3. Upsert the stable `` 🤖 `apptrick-run-ownership` - active run `` marker with this `RUN_ID`, task/spec/repository, `status: active`, and review stage, then re-read it. A mutation or readback failure blocks before review or autofix.

When `labels.enabled` is `false`, the claim consists of the assignee plus the stable ownership marker; other skills detect those two signals.

**Release** (step 12 of the skill body - always, even on failure; use a `trap` or equivalent finally-block so a crash or early stop still clears the lock):

1. When `LABELS_ENABLED` is `true`, remove the `in-progress` label from `{prNumber}` via the tracker operation **unlabel-pr**.
2. Update and re-read the stable ownership marker with terminal `completed` or `aborted` plus the verdict.

The completion comment carries the verdict plus a short summary (and, when autofix ran, how many fix iterations completed). For `changes-requested`, the assignee is already handed back to the author before release; for approved outcomes, keep the current assignee unless a handoff changed it.

**Inherited chain lock (re-entry).** Re-enter only when the stable ownership marker carries this same `RUN_ID` or an explicit handoff. This run keeps the label and assignee signals, updates and re-reads the marker with `status: handoff`, the verdict, and the next stage, and leaves terminal release to the chain driver.
