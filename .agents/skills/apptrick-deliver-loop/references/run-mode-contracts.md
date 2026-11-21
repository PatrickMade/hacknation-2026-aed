# Run-mode contracts (step 1)

What each mode requires once step 1's classification picks it.

## Simple-run contract

For Simple runs, skip the whole run-folder ceremony. Requirements:

- **No run folder**, no `PLAN.md`, no `HANDOFF.md`, no `NOTIFY.md`, no checkpoint files.
- **No Tasks table** anywhere.
- **One code commit** (may be amended pre-push; once pushed, create a new commit rather than amending).
- Unit tests for behavior changes (still mandatory for code; docs-only exempt).
- Targeted checks during implementation, then the full configured `validation.commands` gate before completion. Required integration and QA checks remain mandatory; run affected checks again after review fixes. A failed or unavailable required gate leaves an incomplete draft.
- Conventional-commit subject carrying `TASK_COMMIT_PREFIX`.
- Push and open an incomplete draft; promote to ready only after validation, independent review and required final QA pass. Preserve the inherited issue claim until the PR ownership transfer in `references/claim-pr.md` succeeds.
- Open the PR directly with a short body - `Source doc:` + behavioral change + validation result/limits + rollback only when material (no `Tracking plan:` line, no `Status:` field, no linked run folder).
- Still respect: the inherited isolated worktree on the project-required task branch; the three-signal `in-progress` lock once the PR opens; label discipline (pipeline + category + meta + priority + risk); the single `apptrick-review` pass in autofix mode (breaking-change contract surfaces inside it).
- Final summary comment still posts using `references/summary-comment-template.md`: the run’s delta, verification evidence and next action, without repeating the PR body.

## Spec-implementation-run contract

Keep the full contract documented in the rest of the `SKILL.md` file: run folder, Tasks table, HANDOFF/NOTIFY, checkpoint-based verification, 1:1 step-to-commit discipline, full validation gate before flipping to `complete`, `apptrick-review` autofix pass, outcome and handoff comment using `references/summary-comment-template.md`.

## Promotion path (Simple → Spec-implementation)

A Simple run MAY be promoted to a Spec-implementation run mid-flight if the agent discovers the task is larger than it looked:

- Stop the simple flow.
- Draft the plan under `${RUNS_DIR}/<date>-<slug>/PLAN.md` (with Tasks table, including its `Exec` column), `HANDOFF.md`, `NOTIFY.md`.
- Write a seed commit that adds these files.
- Update the PR body to add `Tracking plan:` and `Status: in-progress` lines.
- Continue under the full Spec-implementation contract from step 2 onwards.

## Spec coverage in both modes

Simple runs still require a proportionate task spec under the preflight gate.
The existence of a short spec alone does not promote a simple task into the
multi-phase mode. Keep existing run-folder and plan formats; bind the task spec
before implementation and carry it into the task worktree.
