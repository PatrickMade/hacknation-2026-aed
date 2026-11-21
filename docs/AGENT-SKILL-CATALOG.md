# Agent skill catalog

Which skill owns each procedure in this repository. Invoke skills by name
(Claude: Skill tool; Codex: `$<skill>`); reading a skill file is not invoking it.

## Sources

- Project edition: the generated `apptrick-` skills in `.agents/skills` and
  `.claude/skills`, pinned by `.ai/apptrick-skills.lock.json` (a frozen project
  copy; `check_project_copy.py` checks it). Edit them only with their lock.
- Project rules: `.ai/skills/apptrick-*/SKILL.md` extensions. The text between
  the `apptrick-harness` markers is the harness copy; add app rules outside
  that block.
- Anything else resolves through `find-skills` from the client's installed
  skills. Prefer the project edition when both have a skill of the same name.

## Routing

| Procedure | Skill |
| --- | --- |
| Harness setup, re-check, Linear provisioning | `apptrick-set-up` |
| Harness upgrade | `apptrick-upgrade` |
| Backlog planning, issues | `apptrick-plan`, `apptrick-create-issue` |
| Task specification | `apptrick-specify` |
| Delivery of one task to a ready PR | `apptrick-deliver` |
| Unfinished planned work on a PR | `apptrick-continue-pr` |
| Review feedback, conflicts, failing CI | `apptrick-fix-pr` |
| Next step for a PR is unclear | `apptrick-advance-pr` |
| Independent PR review | `apptrick-review` (code-only: `apptrick-review-code`) |
| Tests and test environment | `apptrick-test`, `apptrick-prepare-test-env` |
| QA evidence | `apptrick-verify`, `apptrick-guide-qa` |
| Merge through the merge gate | `apptrick-merge` |
| Flutter tests and architecture | `flutter-testing`, `flutter-architecture` |
| iOS Simulator / Android emulator QA | `maestro-cli` |
| Physical device QA | `appium-real-device-testing` |
