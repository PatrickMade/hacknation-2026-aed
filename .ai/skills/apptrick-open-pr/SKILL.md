---
name: apptrick-open-pr
description: "Use when opening or refreshing a pull request with apptrick-open-pr, to target the configured base branch, link the Linear issue and move it to Review."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-open-pr

Apply the installed skill.

- The base is `baseBranch` from `.ai/agentic.config.json` (`auto`: the
  repository's default branch). The PR body names the Linear issue
  (`Refs <KEY>-<n>` and the `Issue:` line; never a GitHub close keyword), the
  spec (`Source doc:`), the platforms, the feature-ledger IDs with their
  scenario states, and the source checks run with their results.
- List native results separately per platform, or state `NOT_RUN`.
- Push one feature branch to the repository bound in `.ai/agentic.config.json`
  through the `personalgit:` remote alias. Never push the base branch or
  tags, never force-push and never use `--no-verify`.
- After the ready PR is open and read back, move the Linear issue to Review
  with `.ai/scripts/apptrick_linear.py transition-issue --to review --from inProgress`,
  which reads the state back (decision D5).
- Step 8 claim transfer follows the apptrick-deliver extension's "Claim and
  release" contract: the issue's ownership marker becomes `released` (naming
  the PR), not `completed`, and Linear writes use only the adapter commands.
<!-- apptrick-harness:end -->
