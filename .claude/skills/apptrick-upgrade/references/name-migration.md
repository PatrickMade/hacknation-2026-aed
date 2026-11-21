# Command-name migration

Run this migration from the shipped skill package even when the repository-root
`UPGRADE_NOTES.md` cannot be read or fetched. It changes project-owned active
navigation only. It does not rename a task, run, branch, worktree, plan, PR,
historical comment, evidence record or completed execution file.

## Shipped names

| Previous command | Current command |
| --- | --- |
| `apptrick-auto-deliver-task` | `apptrick-deliver` |
| `apptrick-discover-product` | `apptrick-discover` |
| `apptrick-spec-writing` | `apptrick-specify` |
| `apptrick-plan-backlog` | `apptrick-plan` |
| `apptrick-prototype-flow` | `apptrick-prototype` |
| `apptrick-design-ui` | `apptrick-design` |
| `apptrick-integration-tests` | `apptrick-test` |
| `apptrick-auto-qa-change` | `apptrick-verify` |
| `apptrick-auto-review-pr` | `apptrick-review` |
| `apptrick-pr-autopilot` | `apptrick-advance-pr` |
| `apptrick-setup-harness` | `apptrick-set-up` |
| `apptrick-upgrade-harness` | `apptrick-upgrade` |
| `apptrick-approve-merge-pr` | `apptrick-merge` |
| `apptrick-ux-review-pr` | `apptrick-ux-review` |
| `apptrick-auto-continue-pr` | `apptrick-continue-pr` |
| `apptrick-auto-fix-pr` | `apptrick-fix-pr` |
| `apptrick-code-review` | `apptrick-review-code` |
| `apptrick-root-cause` | `apptrick-diagnose` |
| `apptrick-fix` | `apptrick-apply-fix` |
| `apptrick-auto-implement-spec` | `apptrick-implement-spec` |
| `apptrick-auto-manage-issues` | `apptrick-refine-issues` |
| `apptrick-auto-create-spec-pr` | `apptrick-publish-spec` |
| `apptrick-auto-update-changelog` | `apptrick-update-changelog` |
| `apptrick-guide-manual-qa` | `apptrick-guide-qa` |
| `apptrick-simulate-user-feedback` | `apptrick-simulate-feedback` |
| `apptrick-pipeline-retro` | `apptrick-improve-workflow` |
| `apptrick-auto-deliver-task-loop` | `apptrick-deliver-loop` |
| `apptrick-auto-continue-pr-loop` | `apptrick-continue-pr-loop` |

All 28 pairs belong to the Development Harness. General ships only current
primary commands and does not use this harness migration. Its retired forwarding
commands are not restored by package upgrades; use the General collection's
own command names directly. General installation and
removal belong to the native skills CLI, without harness setup or tracker operations.

## Reconciliation

1. Inventory active project instructions, scripts and local extensions that use
   either name. Ignore historical specs, completed runs, evidence and tracker
   comments; their original strings are evidence and remain unchanged.
2. For each harness pair, inspect both
   `.ai/skills/<current>/SKILL.md` and `.ai/skills/<previous>/SKILL.md` before a
   dependent mutation. Apply each present extension once. Deduplicate identical
   rules. Treat an import between the two paths as provenance, not another
   invocation.
3. When both extensions contain compatible rules, prepare one reviewed current
   extension that accounts for every rule. Keep the previous extension until
   readback proves the current extension is complete; do not delete it
   automatically. When same-scope rules disagree, show the exact alternatives
   and stop the affected workflow. `--yes` never resolves a conflict.
4. Update active project navigation and caller scripts to the current command.
   Preserve arguments, authority, `RUN_ID`, task reference, spec, worktree,
   branch, PR and completed stages. A current and previous marker in one record
   identify the same workflow; do not create a second run or rewrite the marker.
5. Verify the complete package through its owning installer. Previous commands
   must resolve directly to the current primary with no alias chain. Previous
   helper paths remain forwarding entrypoints and must return the same output and
   exit status as their current target.

Report every changed active caller, every extension path found, conflicts, and
the package verification result. A dry run reports the same inventory and leaves
all files unchanged.
