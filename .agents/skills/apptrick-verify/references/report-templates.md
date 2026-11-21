# Report templates

## Verification report artifacts (step 10)

The machine- and human-readable report artifacts `apptrick-verify` writes
into `$ARTIFACTS_DIR` in every mode (step 10). These are the primary deliverable
in local mode and the source of the PR comment in PR mode.

`$ARTIFACTS_DIR/report.json`:

```json
{
  "runId": "<RUN_ID>",
  "mode": "pr | local",
  "target": { "prNumber": 1234, "title": "…", "branch": "…", "headSha": "…" },
  "verdict": "PASS | FAIL | PARTIAL",
  "environment": { "baseUrl": "…", "role": "…", "startedByThisRepo": true, "browserProvider": "agent-browser | playwright | custom" },
  "scenario": [
    { "step": 1, "priority": "P1", "action": "…", "expected": "…", "observed": "…", "result": "PASS", "screenshot": "step-01-…​.png" }
  ],
  "hasUiTest": false,
  "notes": ["…"]
}
```

`$ARTIFACTS_DIR/report.md` is the authoritative human evidence report, posted
once in PR mode. Retain each required scenario step with expected/observed
results and its screenshot. Keep the introduction short; the table is the
proof. Omit empty notes and repeated descriptions of the PR.

```markdown
## 📸 UI QA evidence - {verdict}

**Verdict:** {✅ PASS | ❌ FAIL | ⚠️ PARTIAL} - {changed behavior exercised and decisive observation or limit}.
**Verified:** {branch} @ {headSha (short)}; `{baseUrl}`, role `{role}`, browser `{provider}`.

| # / Priority | Route and action | Expected | Observed | Result / Evidence |
|--------------|------------------|----------|----------|-------------------|
| 1 / P1 | {route, setup, action} | {expected} | {observed} | {PASS / FAIL / not exercised; screenshot link} |

### 📸 Screenshots
![{screen and state; what this image proves}]({path or url})

### ⚠️ Not exercised
{Only meaningful coverage limits, including missing permissions, empty/error
states, or environmental blockers; say what remains to be checked.}
```

Never fabricate a PASS or omit a required failed/unexercised step to shorten the
report. Report only observations; redact secrets, tokens, `.env` content, and
non-demo credentials in text and screenshots. Omit unsafe screenshots and state
the limitation. Local and PR modes retain this schema.

## Deployed report schema

Deployed mode writes the following additive schema and runs the shipped offline validator. It records accepted and rejected evidence rather than deleting failed proof:

```json
{
  "runId": "<stable run id>",
  "implementationRunId": "<run that produced the deployed candidate>",
  "mode": "deployed",
  "target": { "expectedArtifact": "<approved revision/build/image>", "environment": "<target name>" },
  "observedArtifact": { "identity": "<freshly observed identity>", "observedAt": "<ISO-8601>", "source": "<read-only web/API/CLI/job observation>" },
  "evidenceRevision": "<stable revision for this exact evidence set>",
  "verdict": "PASS | FAIL | PARTIAL",
  "scenarios": [{
    "id": "<stable scenario id>",
    "required": true,
    "surface": "web | api | cli | job",
    "featureCoverage": "<concrete feature behavior this scenario covers>",
    "expected": "<observable result>",
    "actual": "<observed result>",
    "result": "PASS | FAIL | NOT_EXERCISED",
    "capturedAt": "<ISO-8601>",
    "evidence": [{ "kind": "screenshot | api-output | cli-output | job-output", "path": "<existing artifact path relative to report.json or absolute>", "accepted": true, "authOnly": false, "visuallyInspected": true, "capturedAt": "<ISO-8601>" }]
  }],
  "evidenceReview": { "reviewer": "<independent role or human>", "reviewerRunId": "<independent review run id>", "independent": true, "status": "ACCEPTED | REJECTED", "reviewedRunId": "<QA run id>", "reviewedImplementationRunId": "<implementation run id>", "reviewedArtifact": "<identity>", "reviewedEvidenceRevision": "<evidence revision>", "reviewedAt": "<ISO-8601 after all evidence capture>" },
  "notes": ["<rejection reason, limit, or redeploy/retest need>"]
}
```

`featureCoverage`, `accepted`, `authOnly`, and capture times are explicit for every required scenario and evidence item. `visuallyInspected` is required for accepted web screenshots and omitted for non-web evidence. Auth-gate evidence sets `authOnly: true` and cannot satisfy feature coverage. Every referenced evidence path must exist when the validator runs. A rejected item remains in the array with `accepted: false` and a reason in notes. At least one required scenario must exist; optional observations cannot produce PASS by themselves.

## Follow-up UI-test scenario (step 12)

Only when `HAS_UI_TEST` is false: update one follow-up comment in PR mode, or
append it to `report.md` locally. Link the evidence report; do not repeat its
scenario table. Preserve fixture setup, assertions, and cleanup needed to turn
that scenario into a test.

```markdown
## 🧪 Follow-up: add a UI/integration test

Automate [this verified scenario]({evidence link}) with `apptrick-test`:
{fixtures to create}, {scenario steps to reuse}, and {specific assertions}.
Delete every fixture during teardown. {Any additional case the run could not cover}.
```

## Final run report (step 14)

Aim for 3-6 lines plus PR/Issue references. Give outcome, evidence, limitation,
and next action; omit inapplicable fields and routine environment/label details.

```markdown
📸 `apptrick-verify`: {PASS | FAIL | PARTIAL} - {behavior verified and result or blocker}.
Evidence: {PR comment link or local artifacts path}.
{Required coverage left, missing automated-test follow-up, or next QA action}.
{If requested: QA sign-off/failure applied and the evidence that justified it}.
```

Evidence-only runs do not grant QA approval. State that distinction when a
reader could mistake PASS for merge approval. Never duplicate the scenario
or label-rationale comment in the final reply.
