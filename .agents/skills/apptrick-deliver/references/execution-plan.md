# Execution plan and resume contract

Keep the covering spec separate from the execution plan. For one small agreed
change, the plan cites the spec for Goal, Scope, Non-goals and Risks instead of
restating them, and holds only the route evidence, `Source doc:`, `Issue:` and
the Progress checklist. Larger work drafts the full plan with
Goal, Scope, Non-goals, Risks, `Source doc: {repo-relative spec path}`, the route
and its evidence, and `Issue: {TASK_REF} - {TASK_TITLE}` when a task is bound.
Describe the implementation in phases and steps proportional to the change.

Use this exact checklist shape so `apptrick-continue-pr` can resume it:

```markdown
## Progress

### Phase 1: {name}

- [ ] 1.1 {step title}
- [ ] 1.2 {step title}

### Phase 2: {name}

- [ ] 2.1 {step title}
```

The first unchecked row is the resume point. Preserve step ids and titles when
updating progress. After a step's implementation commit, mark it done and append
its real reachable commit SHA using the ASCII separator:

```markdown
- [x] 1.1 {step title} - abc1234
```

Older plans may use U+2014 before the SHA; readers accept either separator, but
new rows use only the ASCII form. Commit the progress update with the project's
task identity and push it with the phase so continuation sees the saved state.
Never mark a step done from a plan or an unexecuted check.

Count these numbered Steps for engine selection before saving the draft. Plain
execution saves it at `PLAN_PATH` and cites that path in the PR's `Tracking plan:`
line. A loop handoff uses its run-folder format instead; do not persist both plan
formats for the same run.
