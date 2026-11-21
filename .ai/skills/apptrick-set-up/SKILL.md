---
name: apptrick-set-up
description: "Use when setting up or re-checking the harness with apptrick-set-up, to apply the catalog routing, the harness package stage and Linear provisioning."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-set-up

## Project skill catalog

Follow `docs/AGENT-SKILL-CATALOG.md` for exact-source procedure routing. Resolve
required procedures through project-aware `find-skills`; preserve native
invocation restrictions and the complete upstream workflow.

For the package install/check stage, run the harness installer of the
pinned harness revision: `tools/install_harness.py --source <trusted harness
checkout> --project .` (and `--check` for read-only verification). It installs
the core and the overlays named in `harness.overlays` of
`.ai/agentic.config.json`. The pinned source and generated Codex metadata are
recorded separately; do not run the raw upstream package installer against
this opted-in tree or silently change its upstream revision.

## Tracker stage

- The tracker is Linear through the adapter `.ai/scripts/apptrick_linear.py`
  (contract `.ai/trackers/linear-adapter.md`), bound to the workspace, team
  and project in `.ai/agentic.config.json`. Read the binding back before any
  write.
- Run, in order: `auth-check`, `states`, `git-automation`, then
  `ensure-taxonomy`, which runs `ensure-label` for every name in the config's
  `labels.*` lists and reads each label back. Every refusal there happens
  before the first create; `UNCERTAIN_WRITE` stops without a replay. Run it
  again after any taxonomy change in the config.
- Create the app's Linear project (`ensure-project`) and its milestones
  (`ensure-milestone`) without asking (decision D6), then read each one back.
  Deleting or archiving anything in Linear needs the owner's approval.
- Keep Linear's GitHub automatic state moves disabled; the harness moves issue
  states itself (decision D5, `SDLC.md` "Linear states").

## Hooks

Route Git hooks to the pinned guard with `sh .ai/scripts/bootstrap-hooks.sh`
(shared clone config, every worktree). A task worktree whose session must not
change the shared config uses `--worktree` instead (`SDLC.md`, "Push guard").

## Existing files

`.ai/agentic.config.json`, the descriptors, `SDLC.md`, `AGENTS.md`,
`CLAUDE.md` and the `.ai/skills` extensions exist and are reviewed. Show a
proposed change as a diff; never regenerate them silently.
<!-- apptrick-harness:end -->
