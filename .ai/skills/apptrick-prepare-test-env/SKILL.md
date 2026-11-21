---
name: apptrick-prepare-test-env
description: "Use when preparing a test environment with apptrick-prepare-test-env, to lease devices and builds through the existing Maestro and Appium skills instead of a web server."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-prepare-test-env

Apply the installed skill. For native app scenarios, select the existing mobile CLI target route described in SDLC.md rather than create a web server. Read maestro-cli or appium-real-device-testing from the shared approved deployment. Resolve exact registered target, installed artifact and existing lease/cache. Existing launchers own provision/install/build/cleanup. Keep runtime bindings in ignored .ai/qa/artifacts_<runId>/, not a new registry. Return explicit target/expected-artifact to apptrick-verify deployed mode. Browser scenarios still use the full configured descriptor.

## Routes

| Target | Owner | Notes |
|---|---|---|
| iOS Simulator | `maestro-cli` | On the Mac. Use `--prepare-flutter-app` when the exact current source is not installed; the same lease owns build, install, run and cleanup. |
| Android emulator | `maestro-cli` | A debug APK is built for that lane. |
| Physical iPhone or Android phone | `appium-real-device-testing` | Lease first (`scripts/appium_real_device_lease.py acquire`); USB devices stay on the local machine. |

## Rules

- Under a coordinator only the QA lane leases, boots and opens devices; an
  owner lane never runs this skill (SDLC.md "Coordinator lanes").
- Open every simulator and emulator in T3 with `device_list` and `device_open`
  so the run is visible. Never steer the same target with agent-device while
  Maestro runs on it.
- Use the exact UDID or serial the launcher leased; never `booted` or a raw
  physical UDID while other agents may be active.
- Test builds use the development or staging environment. Never install a
  production build for ordinary QA.
- Never print or commit signing material, `GoogleService-Info.plist`,
  `google-services.json`, env files or passcodes.
- On failure keep the first failing command, its exit code and log. Never
  change a toolchain pin or digest to make a check pass; that is a reviewed
  change.
- The preparation owner releases leases and stops owned processes after
  verification.
<!-- apptrick-harness:end -->
