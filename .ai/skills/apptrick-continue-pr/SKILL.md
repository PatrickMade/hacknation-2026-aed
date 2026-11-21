---
name: apptrick-continue-pr
description: "Use when continuing an existing pull request with apptrick-continue-pr, to apply the project skill catalog routing."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-continue-pr

## Project skill catalog

Follow `docs/AGENT-SKILL-CATALOG.md` for exact-source procedure routing. Resolve
required procedures through project-aware `find-skills`; preserve native
invocation restrictions and the complete upstream workflow.

## Commits and claims

Commit subjects, claims and Linear writes follow the apptrick-deliver
extension ("Order and commits", "Claim and release"): Conventional Commits
without `TASK_COMMIT_PREFIX`, and Linear writes only through
`.ai/scripts/apptrick_linear.py`.
<!-- apptrick-harness:end -->
