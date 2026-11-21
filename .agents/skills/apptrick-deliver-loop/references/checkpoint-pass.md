# Checkpoint pass (every 5 Steps)

The checkpoint half of step 8. A checkpoint fires when any of these is true:
- 5 Steps have landed since the last checkpoint (or since the start of the run).
- The next Step would close a Phase and the Phase has ≥3 Steps.
- The run is about to hit the final-gate stage (step 9) - that final gate subsumes a checkpoint.
- A blocker stops the run mid-Phase.

At a checkpoint, inspect existing evidence first: run only missing or invalidated checks and required fresh QA; a checkpoint ordinal alone never requires repeating unchanged tests, screenshots or reviews. Preserve result provenance and current-candidate applicability. Record the following in a single `${RUN_DIR}/checkpoint-<N>-checks.md`:

1. **Targeted validation for affected inputs** - inspect per-Step/executor command/result evidence for the areas touched since the last checkpoint. Run only missing or invalidated configured checks, tracing dependent codegen, localization-sync and build inputs. Retain unaffected results with their provenance and current-candidate applicability.
2. **Step review (`engine.stepReview: checkpoint` only)** - review the diff landed since the previous checkpoint per `references/step-review.md`; blocker/major findings are fixed as `X.Y-review-fix` Steps before the checkpoint concludes.
3. **UI verification (conditional)** - if any Step in the window touched UI (pages, components, widgets, navigation):
   - When required integration evidence is missing or invalidated, run the repo's integration suite via the `apptrick-test` skill (running-only mode), scoped to the smallest set covering the affected areas. Reuse valid existing coverage; required fresh QA remains.
   - If no existing test covers the touched area, fall back to browser automation tooling when available to drive a minimal smoke path against the running dev server.
   - Reference existing valid logs/screenshots with their original paths and provenance. Capture missing or invalidated required screenshots under `${RUN_DIR}/checkpoint-<N>-artifacts/`; record applicability in `checkpoint-<N>-checks.md`. A new checkpoint path alone does not require a new artifact.
   - **Post the checkpoint's verification outcome + screenshots to the PR.** The PR exists from step 7, so post immediately (never defer to the run folder alone): an idempotent verification comment - marker `` 🤖 `apptrick-deliver-loop` - checkpoint <N> verification ``, naming the Step range, what the checks proved, pass/fail/skip with material limits, and a link to the checkpoint record; aim for 40-100 words, omit raw logs and repeated scope - and, when a Step in the window touched UI, this checkpoint's screenshots via **attach-image-evidence** - marker `` 🤖 `apptrick-deliver-loop` - checkpoint <N> evidence ``, one line naming the Step range + touched areas, one line per image, slug `checkpoint-<N>`. Both are idempotent by marker: a re-run updates in place. Inline rendering is the tracker descriptor's job; when it cannot, the comment carries links - surface that, don't fail.
   - **UI checks MUST NOT block development.** If the repo has no integration suite, the dev env cannot be started, browser tooling cannot connect, or the scenario requires missing fixtures, skip the UI portion and record a single UTC-timestamped note in `checkpoint-<N>-checks.md` and `NOTIFY.md` explaining why. The checkpoint otherwise proceeds.
4. **Write `checkpoint-<N>-checks.md`** listing: checkpoint index, the Steps it covers (id range + SHA range), touched areas, every check run with pass/fail/skip + reason, and links to any artifacts.
5. **Rewrite `HANDOFF.md`** from scratch with the new state (next concrete action = the first `todo` Step).
6. **Append one NOTIFY entry** for the checkpoint: UTC timestamp, checkpoint index, Step range covered, one-line summary, any decisions/problems.
7. **Commit** the checkpoint files (`checkpoint-<N>-checks.md`, `checkpoint-<N>-artifacts/` if any, `HANDOFF.md`, `NOTIFY.md`) as a single commit: `docs(runs): ${TASK_COMMIT_PREFIX} - checkpoint N steps X.Y..X.Z`. Push.

If the checkpoint fails (typecheck/test/build/integration test regresses), halt shared-checkout dispatch and conflicting integration, rewrite `HANDOFF.md` naming the failure, append a NOTIFY blocker entry, fix forward with new Steps appended to the Tasks table, and re-run the checkpoint before continuing dependent Steps or integration. In isolated execution, unrelated dependency-ready work may proceed; retain the run claim until all active work and pending results are reconciled.

## Resource-scoped parallelism (optional)

- Start authorized dependency-ready independent work without host-capacity admission checks; let the operating system schedule it. Preserve actual tool/provider and explicit user limits, and concrete mutable-resource ownership per Execution resources in `references/rules.md`.
- Give each parallel writer an isolated worktree/branch and separate mutable test resources, including devices, browser contexts, ports, build outputs and data directories. Serialize only actual shared-resource conflicts; keep one controlling owner per concrete resource.
- The main session owns shared plan updates, run claims and integration. Follow the isolated parallel dispatch contract in `references/executor-dispatch.md`; the shared-checkout template remains sequential.
- Record dispatch, observed start, result and integration in `NOTIFY.md`. A returned executor is not an accepted integration or completed task.
