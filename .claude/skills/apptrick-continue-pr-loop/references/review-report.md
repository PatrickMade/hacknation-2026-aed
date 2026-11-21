# Review and report - authoritative automated review pass

Detailed procedure for the single automated review loop of `apptrick-continue-pr-loop`.

## Automated review with `apptrick-review`

Before you post the final summary comment, push the final changes, or flip the PR body to `complete`, subject the resumed PR to its authoritative review with the `apptrick-review` skill. Do not run a separate direct `apptrick-review-code` pass first: `apptrick-review` invokes that engine verbatim and applies compatibility, security, contract, breaking-change, and scope checks.

Update and re-read the stable marker with this `RUN_ID`, `status: handoff`, and review stage. Then invoke `apptrick-review {prNumber} --autofix --run-id "$RUN_ID"`; its inherited path must retain the claim for this loop. Re-read the same marker when it returns and update it to resume finalization. Never release and reclaim between stages.

1. Follow the entire `apptrick-review` workflow verbatim - do not cherry-pick steps.
2. Apply fixes directly in the same worktree used for this resume. Never rewrite earlier commits; always add new commits.
3. Review the corrected delta and unresolved findings in the independent lane, retaining accepted unchanged scope. Loop until `apptrick-review` returns a clean verdict or the remaining findings are non-actionable (out-of-scope, false positive) and explicitly documented in the summary comment you post in step 9.

## Verdict handling

- **Clean verdict** → proceed to the summary comment (step 9); the summary names the verdict and the SHA range of any follow-up commits.
- **Only non-actionable findings remain** → proceed, but list each remaining finding and why it is out of scope or a false positive in the summary comment.
- **Cannot run** (e.g., required checks not yet green, missing context) → stop here, leave `Status: in-progress` in the PR body, update `HANDOFF.md` + `NOTIFY.md` with the blocker, and tell the user how to re-enter.

## apptrick-continue-pr-loop specifics

- The claim check inside `apptrick-review` re-enters only because the stable marker names this same `RUN_ID`; matching current-user identity alone is not authorization.
- Each review fix lands as a **new lean Step** appended to the Tasks table under a fresh `X.Y-review-fix` id: one commit, flip the Tasks row in the same commit, no per-Step checks/handoff files, conventional-commit subject (e.g. `fix(ui): address review feedback on confirmation dialog focus trap`). Push immediately.
- After each batch of fixes:
  - Inspect existing evidence and run affected checks that lack valid results.
  - When the batch closes - or every 5 review-fix Steps, whichever comes first - run a checkpoint pass per step 6b (targeted validation, focused integration tests + screenshots if UI was touched, write `checkpoint-<N>-checks.md`, rewrite `HANDOFF.md`, append NOTIFY entry, commit as `docs(runs): checkpoint N - review fixes`).
  - Run only invalidated checks after corrections; retain unaffected command/result evidence and document its applicability to the corrected candidate. Expand scope through actual dependencies, not module/file count. Do not repeat the full gate solely for another review round.
