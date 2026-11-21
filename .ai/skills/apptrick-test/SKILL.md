---
name: apptrick-test
description: "Use when authoring or running tests with apptrick-test, to use fvm flutter test and repository Maestro flows instead of a browser runner."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-test

Apply the installed skill.

- Unit, widget and golden tests run with `fvm flutter test`; never bare
  `flutter`. Follow the global `flutter-testing` skill, and `tdd` for
  red-green-refactor.
- Integration tests live in `integration_test/`. They need a device, so they
  run on a target leased through apptrick-prepare-test-env, not in the source
  gate.
- End-to-end flows are Maestro YAML in `.maestro/flows/`, bound to catalog
  scenario IDs (`maestroFlow` in `.maestro/scenarios.json`) and
  `Semantics(identifier:)` values. `python3 -B .ai/scripts/scenarios.py validate`
  rejects an empty flow. Run them
  only through `maestro-cli`; physical-device flows use
  `appium-real-device-testing`.
- Never mark a scenario implemented without its flow or test, or
  device-passed without a recorded run on that platform.
- Do not add a browser or Playwright test for a native app screen. Web surfaces
  use the configured `t3-preview` browser descriptor.

## Fresh worktree preparation

A new task worktree has no untracked or generated files, so the validation
gate (`validation.commands`) cannot pass there until it is prepared. Before the
first gate run:

1. `fvm install` when the pinned Flutter SDK is missing, then
   `fvm flutter pub get`.
2. When `pubspec.yaml` lists `build_runner`:
   `fvm dart run build_runner build --delete-conflicting-outputs`.
<!-- apptrick-harness:end -->
