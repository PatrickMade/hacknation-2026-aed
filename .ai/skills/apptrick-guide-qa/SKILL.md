---
name: apptrick-guide-qa
description: "Use when preparing a guided QA runbook with apptrick-guide-qa, to plan per-platform cases and route them to Maestro, Appium or release QA."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-guide-qa

Apply the installed skill.

- The runbook lists each catalog scenario (`.maestro/scenarios.json`) once
  per platform (iOS, Android), with safe test data, configuration, steps,
  expected observations and cleanup. Start from
  `python3 -B .ai/scripts/scenarios.py render --platform <platform> --id <ID>`
  for the IDs `scenarios.py required` names.
- Route each case: iOS Simulator and Android emulator through `maestro-cli`
  and physical devices through `appium-real-device-testing`. Open simulators and emulators in T3 with `device_open`.
- Record the device, OS version and installed artifact identity for every
  result. A human verdict and an AI result stay separate.
- An AI result cites the row from `.ai/scripts/qa_evidence.py` for
  its run (see apptrick-verify "Evidence rows"). The row records the cleanup
  result: lease released and cleanup proven. A failed row, or failed or
  unknown cleanup, keeps the run open.
- Physical-device cases: an iOS Appium run passes its row only with
  `--ios-ipa-path`. Android Appium rows wait for the upstream lease-release
  record, so those cases stay evidence only.
- Labels follow `SDLC.md`: the agent may apply `qa-approved` with
  `qa-self-verified` only through apptrick-verify `--self-qa-signoff`, on a
  non-release change that is not `risk-high`, when every required platform row
  passes (decision D4).
<!-- apptrick-harness:end -->
