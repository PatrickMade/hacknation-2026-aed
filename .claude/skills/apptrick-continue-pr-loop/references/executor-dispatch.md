# Multi-Step runs: executor-dispatch pattern (step 6)

Applies only to **Spec-implementation runs** whose Tasks table marks Steps `dispatch`/`group` (or that hit the legacy fallback below) - Simple runs have at most one code commit and never dispatch.

For the shared-checkout template below, the main session acts as a **dispatcher** and spawns one **executor subagent** per dispatched Step (foreground `Agent` tool call, `subagent_type: "general-purpose"`). The executor implements exactly that Step end-to-end (code commit + Tasks-table flip + push). The main session waits for the executor to return, verifies the commit landed and pushed, then dispatches the next Step.

Placement is decided at planning time: follow the `Exec` column of PLAN.md's Tasks table mechanically - `inline` → drive the Step in the main session with the default per-Step loop; `dispatch[:tier]` → spawn one executor for the Step; `group:<id>[:tier]` → spawn one executor for the whole contiguous group (see Group dispatch below). Do not re-litigate the plan's placement at run time. Plans without an `Exec` column (written before it existed) fall back to the **legacy heuristic**: dispatch each Step when ≥3 Steps are expected to land in this invocation, else run them inline; an empty, `-`, or unrecognized cell falls back the same way for that row, at the default tier.

Hard constraints:

- Subagents do NOT have access to the `Agent` tool. A coordinator subagent **cannot** spawn executors. Dispatch MUST live in the main session.
- Executors using one checkout, branch or shared plan run sequentially. Independent dependency-ready executors may overlap only under the isolated-worktree contract below. Do not add host-capacity admission checks or a fixed count; honor actual provider and explicit user limits and concrete mutable-resource ownership.
- The main session claims the `in-progress` lock **once** at step 1 and releases it **once** at run end (or on early exit). Executors MUST NOT claim or release the lock, and MUST NOT post the final summary comment - both belong to the main session.

## Isolated parallel dispatch

Use this route only when the plan identifies independent, dependency-ready Steps and the execution surface supports separate worktrees. Bind each executor to its own worktree/branch, a verified base revision, exact file scope and private test resources. Keep group member order. If work shares a checkout, mutable files, device, browser profile, port, account state or build output, use the sequential shared-checkout route for that conflict.

For each isolated executor, override the shared-checkout prompt below with these rules:

- Commit only the assigned implementation and test changes on the executor branch. Do not edit the shared PLAN.md, HANDOFF.md or NOTIFY.md, change the run claim, or push the integration branch.
- Return the exact commit SHA, base, changed files and validation evidence. A permitted push targets only the assigned executor branch.
- The main session verifies the returned branch and commit, serializes integration and shared plan updates, resolves conflicts through ordinary reviewed changes, then records the integrated Step SHA in the Tasks table. Do not mark a Step done from dispatch or provider completion alone.
- Run applicable validation and review on the integrated candidate. Start dependent Steps only after their prerequisites are integrated and verified; independent ready work may continue.

For isolated execution, verify one implementation commit per Step between the executor's bound base and returned SHA. Before integrating that result, record the current integration head; afterward verify only this result's accepted change and map its Step to the resulting commit SHA. Do not count unrelated integrations since dispatch. The shared-checkout checklist below applies only to that route. For this route, the shared Tasks-row update is performed by the main session after integration, rather than by the executor. A checkpoint pauses new integration and dependent dispatch until it passes; already-running isolated work may finish and retain its result. Failed work stops its dependent Steps and conflicting writes, without cancelling unrelated isolated work.

## Model tier (best-effort)

When the harness's `Agent` tool supports model selection for subagents, map the Step's tier - `cheap` / `standard` / `capable` - onto the closest model class the harness offers and spawn the executor on it. When it does not, dispatch normally and ignore the tier. Tiers are abstract hints, never model names and never a blocker. Tier resolution: the `Exec` cell's suffix → the `engine.executorTier` config key → `standard`:

```bash
EXECUTOR_TIER=$(jq -r '.engine.executorTier // "standard"' "$CONFIG")
```

The rationale: a Step whose plan text is a complete spec is transcription work - the cheap tier removes the cost reason to keep small independent Steps inline. When a tier was actually applied, name it in the NOTIFY delegation entry.

Executor prompt template - the main session writes this into each spawned `Agent` call:

```markdown
You are an executor for apptrick-continue-pr-loop PR #{prNumber}. Implement exactly one Step.

Working directory: {absolute worktree path}
Branch: {branch} (already checked out; origin tracking set up)
Run folder: {absolute run folder path}

Step to implement:
- Step id: {X.Y}
- Title: {step title from Tasks table}
- Full description: {paste the Step's bullets from PLAN.md Implementation Plan}

Spec anchors:
- PLAN.md: {plan path}
- Source spec: {covering task spec path and relevant section}
- External References adopted: {list from PLAN.md Overview}

Rules:
- One Step = exactly one code commit. Nothing more, nothing less. No docs-flip commit.
- Run affected configured checks that lack applicable evidence. Return the command, exit status, relevant output/evidence pointer and input/environment binding in the existing result so checkpoints can reuse it; no per-Step evidence tree is needed.
- Do NOT write a `step-{X.Y}-checks.md`. Do NOT create a `step-{X.Y}-artifacts/` folder. Verification is checkpoint-based.
- Flip the `Status` cell of row `{X.Y}` in PLAN.md's Tasks table from `todo` to `done` and fill the `Commit` column with the short SHA as part of the same commit (amend if needed to capture the real SHA before push).
- Do NOT rewrite `HANDOFF.md` at the per-Step level. Do NOT append to `NOTIFY.md` unless you hit a blocker, make a scope decision worth logging, or are delegating to another subagent.
- Push after the commit so the remote always has the latest state.
- Do NOT claim or release the `in-progress` lock on the PR, and do NOT post the final summary PR comment. The main session owns both.
- Do NOT rewrite or reorder prior history. Do NOT split into multiple code commits. If this Step truly needs splitting, stop and return early with a report asking the main session to split the Step in PLAN.md first.

Return format (concise report, < 300 words):
- Step id
- Code commit SHA
- Files touched
- Brief note on what changed (one line)
- Check commands, exit status, relevant output/evidence pointers and input/environment binding
- Push confirmation (`origin/{branch}` now at {sha})
- Blockers or decisions worth escalating
```

## Group dispatch

A `group:<id>` set is dispatched as **one executor for the whole group**: when the dispatcher reaches the group's first `todo` member, it spawns a single executor that receives all remaining `todo` members in table order - replace the template's "Step to implement" block with an ordered "Steps to implement" list. Every rule in the selected route applies **per member Step**, in order. Shared-checkout execution uses one code commit + Tasks-row flip + push each; isolated execution returns one implementation commit per member and leaves all shared Tasks-row updates to the main session. Groups are contiguous rows sharing the identical cell value (same tier - one executor, one tier). On resume, dispatch only the group's remaining `todo` members. If any member truly needs splitting, the executor stops and returns early exactly as the single-Step rule says.

Verification the main session MUST run after each executor returns - before dependent dispatch or accepting its integration:

- `git status` is clean in the worktree.
- Exactly **one** new commit **per dispatched Step** exists on HEAD since the dispatch (a group executor returns one commit per member Step).
- Local HEAD == `origin/{branch}` (push actually landed; fetch if in doubt).
- In the shared-checkout route, the PLAN.md Tasks-table row for each dispatched Step is flipped to `done` with the correct short SHA. In the isolated route, verify returned implementation commits first; only the main session writes the row after accepted integration.

When `engine.stepReview` is `per-step`, the main session reviews each dispatched Step's commit range per `references/step-review.md` after this verification passes, before dependent dispatch (a group executor's Steps are reviewed as one range).

Every 5 successfully landed Steps (a group counts each member Step; or when a Phase with ≥3 Steps closes), the main session MUST run a full **checkpoint pass** per step 6b (`references/checkpoint-pass.md`) before integrating further results or starting dependent Steps. Independent isolated work follows the checkpoint policy above.

## Escalation before the stop

A problematic executor result - a returned blocker, failing tests, an error, or a failed post-executor verification - gets **one rescue attempt** before the safety stops fire: restore a clean worktree state (discard the failed executor's uncommitted leftovers; committed prior Steps are never touched), then dispatch a **fresh executor for the same Step one tier above** the failed one (`cheap` → `standard`, `standard` → `capable`), with the failed executor's report and the concrete failure appended to its prompt. The rescue result goes through the same post-executor verification. Escalation is bounded: one rescue per Step, never above `capable` - a Step that already ran at `capable`, or whose rescue also fails, halts per the safety stops below. Append a NOTIFY delegation entry for every rescue, naming both tiers and the failure it answers.

Safety stops - halt the affected shared-checkout run, dependent dispatch and conflicting integration (leave `Status: in-progress`, rewrite `HANDOFF.md`, append a NOTIFY entry naming the blocker, report the affected blocker, and retain the claim while any isolated workers or pending results remain. Release or hand off ownership only through normal whole-run finalization after reconciling all active work) when, after the one rescue attempt above where applicable, any of the following is true:

- An executor returns a blocker, failing tests, or an error - and its rescue also failed or was unavailable.
- `git status` is not clean after an executor returns.
- For shared-checkout execution, the Tasks-table row was not flipped to `done` with the correct SHA. For isolated execution, stop affected integration if the returned commit or evidence fails verification; the main session alone updates the row after integration.
- Local HEAD ≠ `origin/{branch}` (push did not land).

The creator counterpart (`apptrick-deliver-loop`) inherits this pattern when driving multiple Steps in a single invocation.
