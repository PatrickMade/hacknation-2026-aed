---
name: apptrick-verify
description: "Use when collecting QA evidence with apptrick-verify, to run the deployed CLI route on leased simulators, emulators or phones and apply the self-QA rule for non-release changes."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-verify

Apply the installed skill's deployed-target route for native app evidence: --deployed <registered lab target> --expected-artifact <installed identity>. Read references/deployed-target.md and report-templates.md from the installed package. Scope and target allowlists are in SDLC.md and the approved run. Fresh installed-artifact observation must precede every accepted capture; never substitute source HEAD or historic screenshots. Native test operation is the existing Maestro/Appium runner, surfaced as CLI evidence with linked inspected screenshots. Preserve required scenarios, rejected/failed rows, independent review binding and shipped validator. Report narrow pilot acceptance separately from release signoff. No fake URL or web browser is needed for a CLI scenario.

## Project skill catalog

Follow `docs/AGENT-SKILL-CATALOG.md` for exact-source procedure routing. Resolve
required procedures through project-aware `find-skills`; preserve native
invocation restrictions and the complete upstream workflow.

## QA routes

- iOS Simulator and Android emulator: `maestro-cli`, with `--prepare-flutter-app` on iOS.
- Physical iPhone or Android phone: `appium-real-device-testing`.
- This project has no store release route. Simulator or partial evidence
  never grants release acceptance.

## Evidence rows

- Validate every run before citing it:
  `python3 -B .ai/scripts/qa_evidence.py <maestro-cli output dir or appium artifact root> --expected-artifact <identity> [--expected-sha256 <apk sha256>] [--catalog .maestro/scenarios.json]`.
  With the catalog, each flow result names its scenario IDs.
  The identity is `<platform>:<app id>@<build>#<source commit>` for
  `maestro-cli` and `<platform>:<app id>@<version-build>` for Appium. In
  deployed mode the same string is `--expected-artifact`, and the row's
  `identity` is the observed artifact.
- Keep the printed row: platform, device key and name, lease ID, installed
  identity, artifact SHA-256, flow results, lease released, cleanup proven.
  Exit 1 or 2 blocks PASS for that run; keep the row with its `failures`.
- Report rows per platform (iOS, Android) and per catalog scenario ID; one
  platform's PASS does not cover the other. Keep FAIL, rejected and NOT_RUN
  rows with their reasons.
- Appium rows take the runner's `installed_artifact_sha256` and its source.
  An iOS row can pass only when the run used `--ios-ipa-path`; the digest then
  proves which upload was installed, not the on-device bytes. Without it the
  row fails. Android Appium rows fail until the Android lane writes its
  lease-release record (upstream), so they count as evidence only.

## QA verdict

- Scope: `python3 -B .ai/scripts/scenarios.py required --base <base branch> --head <head>`
  names the feature groups and scenario IDs the diff requires;
  `scenarios.py render --id <ID>` gives the tester instructions.
- Record one verdict per platform, pinned to the tested head and the
  installed artifact (`.ai/schemas/qa-verdict.schema.json`), and post the PR
  comment `python3 -B .ai/scripts/qa_freshness.py comment <record>` prints.
  Collect every defect in one pass and record a FAIL verdict at the end of the
  run. A tracked failure is an exception only with its `knownIssue`.
- On a new head, `python3 -B .ai/scripts/rerun_scope.py --tested <sha> --head <sha> --base <base branch>`
  says what runs again. Carried rows are `NOT_RUN` with `carriedFrom`, on the
  same platform only. A script failure is not an app defect: watch the
  recording and report the broken step separately.
- Labels: `python3 -B .ai/scripts/qa_freshness.py check --head <current head> --repo . --base <base branch> <comments>`
  names the label only when the iOS and the Android verdict are both on the
  current head (`qa-approved` when both pass, else `qa-failed`); until then
  nobody labels the PR. A missing SHA is unverified; another head is stale; a
  carried row counts only with an earlier pass on the same platform that
  `rerun_scope.py` lets carry. Under a coordinator only the assigned QA lane
  sets QA labels: the lane that records the second platform verdict. Solo work
  keeps self-QA.
- Under a coordinator the QA lane takes its work from the QA queue file and
  tests the head in its row: when the head moves during QA, stop, record the
  verdict only for the head that was tested and report `QA-VERDICT`. The QA
  lane never pushes; it hands fixes to the owner as a patch file in the
  project's private coordination directory.
- Under a coordinator, carry evidence only when
  `git diff --no-renames --name-only <tested>..<new>` lists only closed-list
  non-app paths; record both SHAs and the path list in the carry record;
  `rerun_scope.py` then picks scenarios. A base update that brought app paths
  needs new QA. Run that diff yourself and check that it equals the
  `changedPaths` of `rerun_scope.py --strict`; the tool never replaces that
  diff. Run `qa_freshness.py check` with `--strict` too. The project sets
  `qa.carryMode: "strict"` on its base branch, so the merge gate checks the
  carry records as well.

## Self-QA (decision D4)

For a non-release change that is not `risk-high`, run with
`--self-qa-signoff` only when every required platform row passes and its
screenshots were inspected. It applies `qa-approved` and `qa-self-verified`
with a `QA head: <sha>` comment. A `risk-high` change, a partial run, a failed
row or a release candidate gets evidence only.
<!-- apptrick-harness:end -->
