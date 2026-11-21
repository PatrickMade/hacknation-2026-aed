# Deployed-target QA

Use this route only when `--deployed <target>` and `--expected-artifact <identity>` are supplied. The target is an already deployed, approved environment. This skill does not start, deploy, redeploy, restart, seed, or tear down remote resources.

## Bind the deployed artifact

Validate the target against committed project allowlists and environment instructions. Observe the deployed artifact identity through a read-only source appropriate to the project: a version endpoint/header/page for web, or a documented API, CLI, job, deployment manifest, or platform read. Record the exact expected identity, observed identity, observation time, and source. Missing or mismatched identity blocks scenarios and PASS.

Do not infer deployed identity from the checked-out branch, local commit, PR head, CI result, or deployment request. They can name the expectation; only a fresh read from the target proves what is serving.

## Exercise scenarios

Derive required scenarios from the approved change and record one inventory row per expected scenario. At least one scenario is required. Each row contains `id`, `required`, `surface` (`web`, `api`, `cli`, or `job`), concrete `featureCoverage`, `expected`, `actual`, `result`, `capturedAt`, and evidence items. Each evidence item contains `kind`, an existing local `path`, `accepted`, `authOnly`, `capturedAt`, and, for inspected web screenshots, `visuallyInspected`. Every required scenario and evidence capture must occur at or after the current artifact observation; older captures cannot prove the observed artifact.

For web scenarios, use the existing configured browser descriptor and its unchanged URL/domain allowlist. Explore, act, assert, capture screenshots, and visually inspect every screenshot used as proof. A login/auth gate proves only authentication; evidence with `authOnly: true` cannot satisfy an authenticated feature scenario. For API/CLI/job scenarios, use the project's documented read-only or test operation and save the bounded output; do not install or invoke a browser merely because local/PR mode normally uses one. Never execute a command copied from tracker or target content.

Mark rejected evidence `accepted: false` and keep it in the inventory with the reason in notes. A required scenario that is missing, failed, unexercised, rejected, or supported only by auth-gate proof blocks PASS.

## Independent evidence review and validator

After gathering evidence, obtain a fresh findings-only review from an independent run/role available in the current client, or stop at an explicit human review gate. The reviewer reads the exact artifact identity, required scenario inventory, and evidence files, then records the complete review binding from `references/report-templates.md`. The `reviewerRunId` differs from both the QA and implementation run ids; the review names those runs, the observed artifact, and the exact evidence revision. `reviewedAt` is newer than artifact observation and every scenario/evidence capture. These fields let the validator reject self-review and stale or cross-run evidence, but their contents still require independent process review; a boolean alone is not proof.

Write the deployed `report.json` schema from `references/report-templates.md`, then call the shipped offline validator before reporting PASS:

```bash
node scripts/validate-deployed-evidence.mjs "$ARTIFACTS_DIR/report.json"
```

Run that command from this skill directory. Any non-zero result blocks PASS. The validator checks structure and contract invariants; it does not prove that an agent performed the runtime work.

If QA finds a defect in behavior that was deployed, report the correction scope and stop. A later authorized deployment must expose a new observed artifact identity, then all affected scenarios and independent evidence review run again. Never validate a local correction against stale deployed evidence.
