# Manual QA report

Write `$ARTIFACTS_DIR/report.md` and return its link. Publication and tracker
changes require a separate authorized operation. Do not record a persistent
knowledge base or claim merge approval.

```markdown
🧪 **AI execution:** {pass | fail | blocked | incomplete}. {Behavior actually exercised and the most relevant result.}
**Human verification:** {not started | partial | completed}, with {pass/fail/skip counts from the current runbook, or unavailable}.

Run: {runId}. Head: {full SHA}. Scenario: {scenarioId}.
Environment: {sanitized UI URL, browser and role}.

## Cases
| Case ID | Scenario | AI result | Human result | Evidence |
| --- | --- | --- | --- | --- |
| {stable ID} | {what was checked} | {pass/fail/blocked/not-run} | {pass/fail/skip/not recorded} | {relative screenshot link} |

## Findings
{Concrete defects with expected/actual behavior and reproduction links, or no findings in the tested scope. Identify unrelated findings separately.}

## Limits and next action
{Untested cases, unavailable evidence and required human action. A skipped case does not count as a pass.}
```

Account for every planned case, including not-run and blocked cases. Bind AI and
human results to the same run, SHA and scenario. If browser-local human results
have not been explicitly supplied, say unavailable; never infer them from AI
results or a screenshot of the controls. Exercising those controls in an agent
test is not human approval. Refer to `$ARTIFACTS_DIR/runbook.html` for completion.

Keep the final chat report short: behavior/result, runbook and report links,
unresolved cases and next action. Never write READY TO MERGE from this skill;
merge readiness also depends on the project's other gates and explicit authority.
