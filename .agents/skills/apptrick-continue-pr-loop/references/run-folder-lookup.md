# Locate the run folder (step 3)

Prefer the explicit `Tracking plan:` line in the PR body (written by `apptrick-deliver-loop`): from the `body` already fetched by the step 1 **get-pr** (no second fetch), take the first line matching `^Tracking (plan|run folder):` (e.g. pipe the body through `grep -E '^Tracking (plan|run folder):' | head -n1`).

Expected value (current format): `Tracking plan: ${RUNS_DIR}/<date>-<slug>/PLAN.md`.

Fallbacks, in order:

1. `Tracking run folder: ${RUNS_DIR}/<date>-<slug>/` - derive `PLAN_PATH` as `${folder}/PLAN.md`.
2. Legacy flat-file format: `Tracking plan: ${RUNS_DIR}/<date>-<slug>.md` - still honored for PRs opened before the folder migration. In this case there is no run folder yet; create one at `${RUNS_DIR}/<date>-<slug>/`, move the flat plan into it as `PLAN.md`, and initialize `HANDOFF.md` and `NOTIFY.md` as part of this resume's first commit.
3. Legacy `Tracking spec:` line (older runs) - accept only a document with an actual legacy execution-plan shape (`## Progress` with numbered checked/unchecked steps). Create the run plan from that execution section; preserve the original covering spec under `SPECS_DIR`.
4. Diff the PR against `origin/$TARGET_BRANCH` and look for a new path under `${RUNS_DIR}/` authored by this branch. If exactly one new plan exists (folder or flat file), use it.
5. Legacy fallback: if no plan under `${RUNS_DIR}/` resolves, inspect specs only for the legacy execution-plan shape defined in fallback 3. A new task spec with an Implementation Plan alone is not a legacy run plan. Build a separate run plan only from a proven legacy execution section; never move or delete the covering spec from `SPECS_DIR`.
6. If multiple candidates were found, stop and ask the user which one to resume.
7. If no tracking plan can be resolved, do not invent one here. Update and re-read the stable ownership marker with `status: handoff`, this `RUN_ID`, and `apptrick-continue-pr` as next stage, retain the assignee and `in-progress` label, then hand it the PR. Its adoption path reconstructs and links the plan from the PR context. If the plan exceeds `engine.loopStepThreshold`, it hands the same run back and this lookup resumes through fallback 2. Do not post a separate handoff heartbeat. If `apptrick-continue-pr` is unavailable, finalize this run as blocked per the claim protocol and report the missing skill.

Record the resolved paths:

```bash
RUN_DIR="${RUNS_DIR}/<date>-<slug>"
PLAN_PATH="${RUN_DIR}/PLAN.md"
HANDOFF_PATH="${RUN_DIR}/HANDOFF.md"
NOTIFY_PATH="${RUN_DIR}/NOTIFY.md"
# Verification is checkpoint-based: ${RUN_DIR}/checkpoint-<N>-checks.md every ~5 Steps.
# Optional artifacts (test logs, screenshots) live at ${RUN_DIR}/checkpoint-<N>-artifacts/.
# Final gate log lives at ${RUN_DIR}/final-gate-checks.md at spec completion.
```
