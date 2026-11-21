# Engine routing - when a run hands off to the loop engine

How `apptrick-deliver` decides whether to run plain or hand the already
investigated task to `apptrick-deliver-loop`. Engine choice never replaces
input validation, existing-work detection, bug diagnosis, feature readiness, or
spec resolution.

## The choice: plain unless the loop is earned

Plain execution is the default - always. The loop engine's run-folder ceremony (PLAN/HANDOFF/NOTIFY, per-step commits, checkpoints) costs several times the tokens of a plain run, so it must be earned.

Hand off to `apptrick-deliver-loop` only when at least one holds:

1. **`--loop` was passed** by the user directly.
2. **The drafted plan exceeds `LOOP_STEP_THRESHOLD` Steps** (`engine.loopStepThreshold`, default 20). Count the Steps (not Phases) drafted in step 7 - the items that would become the Progress checklist rows. More than the threshold → loop.

Nothing else selects the loop: not UI work (plain runs post screenshots via `apptrick-verify` / **attach-image-evidence**), not "might not finish in one pass" (`apptrick-continue-pr` resumes a plain run fine), not subjective "feels large".

## Handoff mechanics

Two trigger paths, one decision. Task intake, claim, isolated worktree, and the
covering spec may already exist, but no implementation edit or plan commit lands
before engine selection:

- **`--loop` passed** → finish input resolution, existing-work detection, route
  classification, investigation, and spec resolution; then draft the handoff
  plan and delegate before saving a plain Progress plan.
- **Otherwise** → after drafting the execution plan but **before saving it**:
  count the Steps; over the threshold → hand off; else save and continue plain.

Invoke `apptrick-deliver-loop` from the already-owned isolated worktree with `"$TASK_BRIEF"`, forwarding `--issue "$TASK_REF"` when bound, `--run-id "$RUN_ID"`, `--spec "$SPEC_PATH"`, `--slug ${SLUG}`, every `--skill-url`, and `--force` when given. Do not invent or forward unsupported `--interactive` or `--no-ui` options: resolve interactive spec questions before the handoff and record the optional UI-evidence decision in accepted task/spec/handoff input. Do not forward `--original-estimate` after an issue is bound: the loop reuses the canonical issue and never creates or edits it. The drafted Progress-format plan is discarded - it was never written or committed - and the loop verifies and reuses the current worktree, branch, spec bytes, task and run id before deriving its run-folder `PLAN.md`. It never resets the worktree or creates a duplicate task/PR. After acceptance, the loop owns finalization of the inherited issue/PR claims and worktree; the primary must not release or clean them a second time. If handoff fails before acceptance, the primary retains cleanup responsibility. After the loop completes, relay its report and chaining lines unchanged, prefixed with the `Engine:` line.

## The Engine report line

State the decision in one line in the run report and PR summary comment: `Engine: <name> (steps: <N>, --loop: <yes|no>)`. `<N>` is the count that informed the decision - the drafted plan's Steps, or `n/a` when `--loop` forced the handoff before a plan was drafted. Never reworded; callers relay it verbatim.

## Consequence for the plan format

The engine is decided **before** any plan is committed, because the two engines consume different plan formats: plain → the standard Progress-tracked execution plan (per `apptrick-deliver` step 7); loop → the run-folder in `apptrick-deliver-loop`'s format (`PLAN.md` Tasks table + `HANDOFF.md`/`NOTIFY.md`). A run's format is therefore fixed at creation - resume plain PRs with `apptrick-continue-pr`, and run-folder PRs with `apptrick-continue-pr-loop`. A pushed current-format plain plan without a PR resumes per `references/task-routing.md` section 1 (open the draft PR, then `apptrick-continue-pr`); other pre-PR plans and run folders stop for manual recovery. Never re-apply the threshold to a run that already has artifacts.
