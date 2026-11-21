---
name: apptrick-simulate-user-feedback
description: "Compatibility alias for apptrick-simulate-feedback. Use when the previous command apptrick-simulate-user-feedback is requested."
metadata:
  deprecated-alias-for: apptrick-simulate-feedback
---

# Compatibility alias for `apptrick-simulate-feedback`

Use `apptrick-simulate-feedback` for new work. This previous command remains available for at least
one release cycle and does not define a separate workflow.

## Arguments and chaining

Forward the original arguments unchanged, including issue references, estimates,
inspection intent, publication limits and the inherited `RUN_ID`. Preserve the
bound task, repository, spec, worktree, PR and completed stages.

## Workflow

1. Resolve the installed `apptrick-simulate-feedback` skill by name and read its entrypoint.
   If the primary skill is missing, stop and name it; do not fetch a replacement.
2. Delegate once to `apptrick-simulate-feedback` within the user's original task and authority.
   Its preflight owns task specs, ownership, validation and current and previous-name
   local extensions. Do not start a second task or run.
3. Relay its actual result and chaining fields unchanged. Preserve historical
   comment markers; do not post a migration or coordination comment.

## Rules

The primary skill owns every action and permission check. This alias must not
relax its requirements. Before delegation, do not perform tracker or repository
mutations. Read-only requests remain read-only; a previous command grants no extra
merge, deployment, credential or global-install authority.
