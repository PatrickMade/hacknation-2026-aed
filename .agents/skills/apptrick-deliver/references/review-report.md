# Review and report - authoritative automated review pass

Detailed procedure for step 10, the single code-review/autofix loop of `apptrick-deliver`.

## Automated review with `apptrick-review` (step 10)

Before you post the final summary comment, push the last commits, or report back, subject the PR to its authoritative review with the `apptrick-review` skill. Do not run a separate direct `apptrick-review-code` pass first: `apptrick-review` invokes that engine verbatim and adds the autofix loop.

`apptrick-deliver` passes the stable `RUN_ID` when it chains into `apptrick-review`. The review claim check runs **first, before any review work**: it either claims a clear PR for that run or re-enters only when the stable ownership marker names that same `RUN_ID` or an explicit handoff. A matching account, assignee, or PR author never authorizes re-entry. An active marker for another run or incomplete ownership history blocks before review or autofix. It releases only a claim its own run opened, per its workflow (see `references/claim-pr.md`, chained hand-off).

Invoke `apptrick-review {prNumber} --autofix --run-id "$RUN_ID"` so explicit fix authority and the inherited ownership id are both preserved:

1. Require its fresh-context, read-only independent reviewer; this caller owns fixes. If unavailable, keep the PR incomplete and draft. Follow the entire `apptrick-review` workflow verbatim - do not cherry-pick steps.
2. When it flags actionable issues, apply fixes directly in the same worktree used for this run. Never rewrite earlier commits; always add new commits.
3. After each batch of fixes:
   - Inspect existing evidence and run the affected checks that lack valid results.
   - Run only invalidated checks after corrections; retain unaffected command/result evidence and document its applicability to the corrected candidate. Expand scope through actual dependencies, not module/file count. Do not repeat the full gate solely for another review round.
   - Update the plan's **Progress** section if the fix corresponds to a plan Step (flip `- [ ]` to `- [x]` with the commit SHA); otherwise add a short note under the relevant Phase heading in the plan (e.g. `- [x] Post-review fix: {one-line summary} - {sha}`).
   - Commit using a clear conventional-commit subject carrying `TASK_COMMIT_PREFIX` (e.g. `fix(ui): ${TASK_COMMIT_PREFIX} - address confirmation dialog focus`). Push immediately.
4. Review the corrected delta and unresolved findings in the independent lane, retaining accepted unchanged scope. Loop until `apptrick-review` returns a clean verdict (no actionable blockers) or the remaining findings are non-actionable (out-of-scope, false positive) and explicitly documented in the summary comment you post in step 11.

## Verdict handling

- **Clean verdict** → proceed to the summary comment (step 11); the summary names the verdict and the SHA range of any follow-up commits.
- **Only non-actionable findings remain** → proceed, but list each remaining finding and why it is out of scope or a false positive in the summary comment.
- **Cannot run** (e.g., required checks not yet green, missing context) → escalate: leave `Status: in-progress` in the PR body, stop here, and report the blocker to the user so they can decide whether to resume via `apptrick-continue-pr`.
