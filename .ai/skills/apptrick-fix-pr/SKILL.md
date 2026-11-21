---
name: apptrick-fix-pr
description: "Use when driving a pull request to merge-ready with apptrick-fix-pr, to scope its target-branch merge under a coordinator."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-fix-pr

Apply the installed skill with this change.

- **Target merge under a coordinator.** When this PR's owner lane runs
  under a coordinator, merge the PR's target branch into it only for a
  conflict GitHub shows, a dependency on a newly merged PR, or the update
  right before merge (SDLC.md "Coordinator lanes").
  Otherwise skip step 3 ("Merge the latest target branch in - first",
  `references/base-merge.md`), the "Target first" rule and the stabilization
  loop's re-merge when the target advanced (`references/stabilize-ci.md`
  step 4), and in stage (1) let `apptrick-review --autofix` merge the target
  only in those cases: review and CI judge the PR head as it is. Solo work
  keeps the installed order.
- Under a coordinator the owner lane passes `--no-ui`: device QA is the QA
  lane's.
<!-- apptrick-harness:end -->
