---
name: apptrick-auto-continue-pr
description: "Compatibility alias for apptrick-continue-pr. Use when the previous command apptrick-auto-continue-pr is requested."
metadata:
  deprecated-alias-for: apptrick-continue-pr
---

# Compatibility alias for `apptrick-continue-pr`

Use `apptrick-continue-pr` for new work. This previous command remains available for at least
one release cycle and does not define a separate workflow.

## Arguments and chaining

Forward the original arguments unchanged, including issue references, estimates,
inspection intent, publication limits and the inherited `RUN_ID`. Preserve the
bound task, repository, spec, worktree, PR and completed stages.

## Workflow

1. Resolve the installed `apptrick-continue-pr` skill by name and read its entrypoint.
   If the primary skill is missing, stop and name it; do not fetch a replacement.
2. Delegate once to `apptrick-continue-pr` within the user's original task and authority.
   Its preflight owns task specs, ownership, validation and current and previous-name
   local extensions. Do not start a second task or run.
3. Relay its actual result and chaining fields unchanged. Preserve historical
   comment markers; do not post a migration or coordination comment.

## Rules

The primary skill owns every action and permission check. This alias must not
relax its requirements. Before delegation, do not perform tracker or repository
mutations. Read-only requests remain read-only; a previous command grants no extra
merge, deployment, credential or global-install authority.
