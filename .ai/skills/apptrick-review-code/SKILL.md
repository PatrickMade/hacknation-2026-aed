---
name: apptrick-review-code
description: "Use when assessing a diff with apptrick-review-code, to add the Flutter, platform, evidence and harness checks to the installed checklist."
---

<!-- apptrick-harness:begin -->
# Harness extension for apptrick-review-code

Apply the installed skill, `AGENTS.md` and `CODE_REVIEW.md` when present. Also
check:

- A native-impacting diff names iOS and Android and its feature-ledger IDs.
  Every changed behavior updates its ledger entry, Maestro flow, test and
  evidence links together, or has a planned row. No broader planned scenario
  was dropped.
- `AGENTS.md` laws the diff touches hold, including `fvm flutter` only and
  ARB strings with no hardcoded `Text('...')`.
- Automation targets use `Semantics(identifier:)`; flows use no coordinate taps.
- No credentials, env files, signing material or Firebase config files are
  committed. Development, staging and production identities are not swapped.
- The PR does not claim installed-app results from source tests; native
  results are listed per platform, or `NOT_RUN`.
- No dead or unreferenced code, unused files or scripts, duplicated logic,
  stale docs or specs, or leftover compatibility paths. A replacement removes
  what it replaces; anything kept names its consumer and removal condition.
- Commit subjects follow the apptrick-deliver extension rule.
- Installed package files (`.agents/skills`, `.claude/skills`) are never
  hand-edited; project rules live in `.ai/skills` extensions.
<!-- apptrick-harness:end -->
