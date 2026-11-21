---
name: apptrick-upgrade
description: "Use when upgrading the installed skill package or harness with apptrick-upgrade, to apply the catalog routing and the harness package stage."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-upgrade

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
<!-- apptrick-harness:end -->
