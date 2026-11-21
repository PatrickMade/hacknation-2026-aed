# Review and report - authoritative automated review pass

Detailed procedure for step 7, the single automated review loop of `apptrick-continue-pr`.

## Automated review with `apptrick-review` (step 7)

Before you post the final summary comment, push the final changes, or flip the PR body to `complete`, subject the resumed PR to its authoritative review with the `apptrick-review` skill. Do not run a separate direct `apptrick-review-code` pass first: `apptrick-review` invokes that engine verbatim and applies compatibility, security, API-contract, breaking-change, and scope checks.

Invoke the `apptrick-review` skill against `{prNumber}` in autofix mode:

1. Follow the entire `apptrick-review` workflow verbatim - do not cherry-pick steps.
2. When it flags actionable issues, apply fixes directly in the same worktree used for this resume. Never rewrite earlier commits; always add new commits.
3. After each batch of fixes:
   - Inspect existing evidence and run the affected checks that lack valid results.
   - Run only invalidated checks after corrections; retain unaffected command/result evidence and document its applicability to the corrected candidate. Expand scope through actual dependencies, not module/file count. Do not repeat the full gate solely for another review round.
   - Update the plan's **Progress** section when a fix corresponds to a plan Step (flip `- [ ]` to `- [x]` with the commit SHA); otherwise add `- [x] Post-review fix: {one-line summary} - {sha}` under the relevant Phase heading.
   - Commit using a clear conventional-commit subject (e.g. `fix(ui): address review feedback on confirmation dialog focus trap`). Push immediately.
4. Review the corrected delta and unresolved findings in the independent lane, retaining accepted unchanged scope. Loop until `apptrick-review` returns a clean verdict (no actionable blockers) or the remaining findings are non-actionable (out-of-scope, false positive) and explicitly documented in the summary comment you post in step 8.

## Verdict handling

- **Clean verdict** → proceed to the summary comment (step 8); the summary names the verdict and the SHA range of any follow-up commits.
- **Only non-actionable findings remain** → proceed, but list each remaining finding and why it is out of scope or a false positive in the summary comment.
- **Cannot run** (e.g., required checks not yet green, missing context) → stop here, leave `Status: in-progress` in the PR body, document the blocker in the summary comment, and tell the user how to re-enter (`/apptrick-continue-pr {prNumber}`).

## apptrick-continue-pr specifics

- Lock re-entry: `apptrick-review`'s claim check recognizes that the current user already owns the `in-progress` lock from step 1, so it proceeds as re-entry without re-claiming. This skill keeps owning the lock and releases it in step 9.
