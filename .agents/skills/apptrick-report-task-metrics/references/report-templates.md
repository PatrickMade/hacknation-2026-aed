# Report and handoff

Use this template in step 6; omit empty optional sections and keep machine fields.

```text
🤖 `apptrick-report-task-metrics` - task metrics
<Task outcome and what the measured evidence supports, in one sentence.>

🧪 Measurements
<Delivery duration, summed actor activity, tokens and API-equivalent cost where
available; label reconstructed values, known subtotals and reporting overhead.>

⚠️ Coverage
<Expected/covered/missing/duplicate counts and material unavailable metrics.>

🔁 Publication
<Stored receipt, explicit local-only intent, or pending cause and retry artifact.>

Metrics report: <local report path>
Metrics status: complete|partial|blocked
Publication status: stored|pending|local_only|not_written
```

`Metrics status: complete` requires all applicable task measurements and source
coverage; publication can independently remain pending. Required missing input
or an identity/validation conflict is blocked. In inspect mode omit the artifact
line because no report was written, and describe observed coverage only.

Relay only existing, evidence-backed chaining lines at the end, one per line:

```text
PR: #<number> (link: <full PR URL>)
Issue: #<number> (link: <full issue URL>)
Spec: <repo-relative path>
```

For Jira/Linear use `Issue: <native-key> (link: <full issue URL>)`. Omit absent
fields. These are handoff references, not authority to edit or notify trackers;
this skill posts no comments or label changes.
