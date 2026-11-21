---
name: apptrick-advance-pr
description: "Use when driving a pull request with apptrick-advance-pr, to keep merges behind the merge gate and to apply the coordinator lane rules."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-advance-pr

Apply the installed skill with these changes.

- **Merge gate.** `--allow-merge` ends in a merge only through
  `apptrick-merge`, which merges with
  `python3 -B .ai/scripts/merge_gate.py --pr <number> --author-session <authoring session> --merge`
  (apptrick-merge extension). The gate refuses `in-progress`, so before the
  merge step remove this run's own `in-progress` label (keep the assignee and
  the claim comment as the lock). Then run the gate without `--merge`; a
  refusal stops the chain at merge-ready and the report lists every
  refusal. `in-progress` is not put back after a refusal: the run reports
  and releases its claim as usual.
- **Delivery mode.** `delivery.mode` in `.ai/agentic.config.json` decides
  (default `autonomous`). Under `human-gated` the run never merges: it stops
  at merge-ready, even with `--allow-merge`.
- **Under a coordinator.** The PR's owner lane passes `--allow-merge` only when
  the coordinator's merge-order file allows that PR: its dependencies are
  merged and no higher-listed PR is green at the same time. An owner lane never
  dispatches `apptrick-verify` or a device: QA is the QA lane's (SDLC.md
  "Coordinator lanes").
- **Base merge under a coordinator.** State-matrix row 4 (conflicting or
  behind the base) dispatches `apptrick-fix-pr` for a base merge only for a
  conflict GitHub shows, a dependency on a newly merged PR, or the update
  right before merge (SDLC.md "Coordinator lanes"); being behind the base is
  no reason before that (apptrick-fix-pr extension).
- **Independent review.** An authoring session never dispatches
  `apptrick-review` on its own PR; the record comes from another session
  (apptrick-deliver extension, "Independent review").
<!-- apptrick-harness:end -->
