# Spec Delta (steps 6 and 7)

Use this file when a spec is being written for the change (the small-change rule
decides that, not this file) and the change adds, changes or removes behavior a
user, caller or operator can observe. Skip it for refactors, tooling and
docs-only changes. The Delta makes the behavior change reviewable in one place:
a reviewer and the QA step read what is new, what changes and what goes, with
acceptance written as scenarios.

## Delta section shape

```markdown
## 📝 Delta

### ADDED: {behavior name}
The system {does the new observable behavior}.
- WHEN {condition}
- THEN {observable outcome}

### MODIFIED: {behavior name as users know it today}
Today: {current behavior, read from the code}.
Now: {the full replacement behavior, not a diff}.
- WHEN {condition}
- THEN {observable outcome}
Frozen by: `{repo-relative path of an existing test}` | intended change

### REMOVED: {behavior name}
Reason: {why the behavior goes, and what replaces it if anything}.
Frozen by: `{repo-relative path of an existing test}` | intended change
```

- One entry states one behavior and carries at least one `WHEN`/`THEN` scenario.
  A rule that cannot be phrased as an observable scenario is design detail and
  belongs in Architecture.
- The `Today:` line describes the code, not a prior spec (`references/prior-specs.md`).
- A rename is a `REMOVED` of the old name plus an `ADDED` of the new one.
- Acceptance criteria may point at the scenarios instead of repeating them.

## `Frozen by:` (optional)

`Frozen by:` tells the reviewer what already protects today's behavior:

- an existing test path that asserts the current behavior, which the change then
  updates (`MODIFIED`) or deletes with the behavior (`REMOVED`), so the test diff
  shows the behavior change; or
- `intended change` when no test pins the old behavior and the change is the
  point of the task.

Add a new characterization test (assert today's behavior, green on unchanged
code) only when the behavior is risky and no existing test protects it, for
example a `risk-high` area from the project's high-risk diff table. Name the
realistic defect it would catch. Otherwise reuse existing coverage; the Delta
does not add a phase step or a test per entry.

## What review does with it

A reviewer uses the Delta to check that the diff matches the stated behavior
change. A missing Delta entry or a missing `Frozen by:` line is not a finding on
its own; report a finding only when the diff changes observable behavior in a
way the spec contradicts or that its acceptance criteria do not cover.
