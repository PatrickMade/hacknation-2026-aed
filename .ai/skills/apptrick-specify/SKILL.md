---
name: apptrick-specify
description: "Use when writing a task spec with apptrick-specify, to add the Linear key, platforms, feature-ledger IDs and QA route."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-specify

Apply the installed skill. Keep the installed file name
(`.ai/specs/<YYYY-MM-DD>-<slug>.md`) and put `Issue: <KEY>-<n>` on the first
lines when a Linear issue exists.

An application spec also records:

- platforms: iOS and Android, unless the app blueprint limits one (for
  `iphone_only`, iPhone form factor on iOS plus Android);
- the feature-ledger entries it changes (`docs/features/APP_FEATURES.md` and
  `docs/features/features/*.md`), with their behavior, flow and automation IDs;
- the scenario IDs it adds or changes in the catalog
  (`.maestro/scenarios.json`), and the feature groups whose required IDs it
  needs, by group name (`scenarios.py required`), not as a copy of their IDs;
- the Maestro flows (`.maestro/flows/*.yaml`) and `Semantics(identifier:)`
  values it adds or changes;
- each scenario's state: planned, source-implemented, simulator-passed or
  device-passed, and the broader planned scenarios it leaves open;
- the QA route: simulator or emulator through `maestro-cli` or physical device
  through `appium-real-device-testing`;
- release impact: none, or the release candidate it belongs to.

Internal engineering and documentation tasks get no artificial product
scenarios.
<!-- apptrick-harness:end -->
