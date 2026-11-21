# Claiming and releasing work - issues and PRs

The generalized claim/lock procedure for any tracker item (issue or PR) an autonomous run takes ownership of. All reads and mutations go through the tracker descriptor's operations; label mutations only through the `apply_label` guard. This complements the skill-specific slot check (run folder / branch / open PR - see the specifics section below) - the slot check decides whether the *work* exists, this procedure decides who *owns* it.

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
3. Upsert the stable ownership marker through **list-issue-comments** plus **update-comment** (or the equivalent PR conversation operations), then re-read it before work:

   `` 🤖 `apptrick-run-ownership` - active run `` followed by the minimal cross-host fields defined above.

## Release / handback

When the run finishes, hands off, or aborts:

- Update the local context and stable ownership marker first: `handoff` while the same run continues in another skill; otherwise the terminal `completed`, `aborted`, or `released` outcome. Include the last completed stage, upsert the same marker through **update-comment**, and read it back. A terminal marker never remains `active`, including when labels are disabled.
- Remove the `in-progress` label via the guard - and when the run intends to follow up with CI results after reporting, **swap** rather than simply remove: `apply_label "ci-monitoring"` in the same breath, so the item is never observably unlabeled and the outstanding follow-up is visible. Remove `ci-monitoring` when the CI-result comment is finally posted, or when the CI wait is abandoned at its `ci.maxWaitMinutes` cap (nobody is monitoring then, and leaving the label would promise a follow-up that never comes). A run that does no CI follow-up at all just removes `in-progress` as before and never applies `ci-monitoring`.
- In issue-driven runs, hand the issue back: restore the original assignee/author when the pipeline convention expects it.
- Post a short release comment stating the outcome (PR opened with its number, blocked with the blocker, or no action needed).
- The claimant releases their own claim - never release a lock another agent holds. A sub-skill that claims for itself (e.g. a standalone `apptrick-review` run) owns its own release; under a chained hand-off the sub-skill instead re-enters and retains the lock (see Chained hand-off below). Do not second-guess either.

## Chained hand-off - a live chain never drops its lock

When the same run (same `RUN_ID`) finishes one skill and continues on the same item with another - `apptrick-open-pr` → `apptrick-review`, review → UI QA, or any flow-runner chain - the lock is **transferred, never released and re-acquired**. A release-then-reclaim seam leaves the item observably unclaimed mid-run: any concurrent actor's three-signal check reads "not in progress" and legitimately starts duplicate work, and humans watching the tracker see no owner and no state.

- **Hand-off (finishing step):** keep the `in-progress` label and lock assignee in place; update the stable ownership marker with the next phase and last completed stage. Post no hand-off heartbeat comment:

  Legacy consumers may still parse this prior hand-off marker, but new runs do not emit it.

- **Take-over (next step):** re-read the stable ownership marker and require this `RUN_ID`; before any other work, update its stage and local run context.

  Legacy consumers may still parse this prior take-over marker, but new runs do not emit it.

- **Ownership:** a skill releases only a lock its own run opened. An inherited (handed-off) lock is annotated in the completion comment (`Lock retained - chain continues.`) and released by the chain's driving skill at the end of the run, or by its failure path - "the claimant releases their own claim" applies to the chain as a whole.
- **Crash recovery (adoption):** unknown or legacy ownership is never same-run re-entry. A standalone run may adopt only after the documented stale window and activity checks, or through an explicit handoff/`--force`; update the stable ownership marker before work and own its final release. Preserve other worktrees, processes, and browser sessions.
- **Invariant:** an item under active automation is never observably unclaimed: the stable marker update precedes work, and its handoff or terminal update is the stage's last ownership mutation.

## apptrick-deliver-loop specifics

### Pre-flight run-ownership (slot) check - step 2

Before writing anything, confirm no other run owns the slot. Resolve `CURRENT_USER` via **current-user**. Preserve the verified handoff's `DATE`, `SLUG`, `BRANCH`, `RUN_ID`, task binding and worktree; missing or mismatched values block. Derive only the loop artifact paths:

```bash
RUN_DIR="${RUNS_DIR}/${DATE}-${SLUG}"
PLAN_PATH="${RUN_DIR}/PLAN.md"
HANDOFF_PATH="${RUN_DIR}/HANDOFF.md"
NOTIFY_PATH="${RUN_DIR}/NOTIFY.md"
# Verification is checkpoint-based: ${RUN_DIR}/checkpoint-<N>-checks.md every ~5 Steps.
# Optional artifacts (browser transcripts, screenshots) live at ${RUN_DIR}/checkpoint-<N>-artifacts/.
# Final gate log lives at ${RUN_DIR}/final-gate-checks.md at spec completion.
```

Branch naming comes from the already-validated project task branch. Do not derive
or reset a branch in this engine. The fresh branch reserved by the verified
handoff is this run's own slot, not a legacy run to resume. Existing plan/run
artifacts or a PR still require the decision below.

A run is **already in progress** when ANY of the following is true:

- A folder at `$RUN_DIR` (or a legacy flat file `${RUN_DIR}.md`) already exists on `origin/$BASE_BRANCH` or any remote branch.
- A remote branch `origin/${BRANCH}` already exists.
- An open PR already references `$RUN_DIR` or `$PLAN_PATH` (check via **search-prs** with the run-folder path as the query, or by scanning open PRs via **list-prs**).

Decision tree:

| State | `--force` set? | Action |
|-------|---------------|--------|
| Nothing exists | - | Claim and proceed. |
| Existing implementation PR, the same `RUN_ID` owns it | - | Hand off to `apptrick-continue-pr-loop` with its PR number and stop. |
| Existing plan/run artifacts without a PR | - | Preserve them and stop for manual recovery. |
| Run folder/branch exists, someone else owns it | no | **STOP.** Ask the user: "Run folder/branch for `${SLUG}` already exists (owner: ${owner}). Override and continue?" Only continue when the user explicitly says yes. |
| Run folder/branch exists, someone else owns it | yes | Pick a new dated slug (`${SLUG}-v2` or append a time suffix) to avoid clobber; document in the new `PLAN.md` why the original was superseded. |

When an open PR already references the run folder and its marker names this `RUN_ID`, stop and tell the user to use `apptrick-continue-pr-loop {prNumber} --run-id "$RUN_ID"` instead. A different or unreadable run identity remains a conflict.

### PR lock lifecycle - steps 7 to 13

This skill holds one continuous run-owned claim from the moment the draft PR opens until an explicit continuation handoff or terminal finalization:

1. **Claim (step 7, immediately after opening the draft PR):**
   1. **assign-pr** - add `$CURRENT_USER` as assignee.
   2. **label-pr** - apply `in-progress` through the `apply_label` guard. When labels are disabled, assignee plus marker remain the two available signals.
   3. **list-issue-comments / update-comment** - upsert the stable ownership marker with this `RUN_ID`, task/spec/repository, `status: active`, and implementation stage, then re-read it. Any incomplete history, mutation failure, or readback mismatch blocks before implementation.
   4. If the primary handed over an issue claim, keep it until the PR marker has
      been re-read successfully. Then update and re-read that issue marker as
      `status: released`, naming this PR and the same `RUN_ID`, and remove only
      its owned `in-progress` signal. The PR remains continuously claimed. If any
      mutation/readback is uncertain, stop without replay or a successful-release
      claim. On failure before transfer, the loop owns terminal `aborted` cleanup
      of the inherited issue claim; release only after verified marker readback.
2. **Review handoff (step 11):** keep the assignee and `in-progress` label, update the stable marker to `status: handoff` and the review stage, then re-read it. Invoke `apptrick-review --autofix --run-id "$RUN_ID"`; its inherited path requires the same `RUN_ID` and retains the claim.
3. **Return from review (step 11):** re-read and require the same marker before any fix or summary work, update its stage back to the outer loop, and re-read it. Never remove and reapply a signal between these stages.
4. **Finalization (step 13):** for a completed or non-resumable failed run, update the stable marker to terminal `completed` or `aborted` with the last completed stage, re-read it, then remove `in-progress`. For a resumable run, update and re-read `status: handoff` with this `RUN_ID` and `apptrick-continue-pr-loop` as next stage; retain the claim signals. A marker mutation/readback failure blocks label removal and a successful-release report.

Executor subagents (see `references/executor-dispatch.md`) MUST NOT claim, hand off, or release this lock - the main session owns it.
