## CI completeness at the current head

In PR mode, read the current PR `headRefOid`, **get-pr-checks**, **get-required-checks**, and
**list-runs**, selecting runs for that exact head SHA. A short or empty job list
is not evidence that CI passed: queued workflows may not have registered jobs.
Require both job and run readings to agree before a green verdict. An applicable
required workflow that is queued/running is pending; a completed failed,
cancelled, timed-out or action-required run is not passing. Use the latest attempt
of each applicable workflow so an old failed attempt does not defeat a successful
rerun. Respect the project's required-check policy; do not promote optional checks
to required when that policy is readable. If protection is unreadable, retain the
descriptor's conservative required-check fallback.

Missing expected runs or incomplete/unreadable responses mean unverified, never
green. A skipped workflow is acceptable only when the project's configured policy
and observed filter/skip result explain it; do not infer a skip from absence.
Re-read the head before concluding; a changed SHA starts a new assessment. Poll
within the existing CI time budget, then report pending/unverified. Do not delay
normal delivery reporting or ready-for-review promotion just to wait for CI;
merge readiness still requires genuinely passing required checks. A provider
without run-level visibility must disclose that gap instead of claiming complete
CI verification. Report the assessed SHA and the check/run evidence.

## Executable assessment

Normalize observed tracker responses into JSON and run this skill's own
`node scripts/assess-verification.mjs < evidence.json`. Retain its result with
the evidence. Exit zero means readable input, not PASS: require `status: pass`.
Do not fabricate completeness or expected checks to obtain a passing result.

CI input: `kind: ci`, `mode: pr|branch`, `head`, `observedHead` (fresh reread),
`checksComplete`, `runsComplete`, `requiredChecks` (names, or null for conservative
fallback), `expectedWorkflows` (required names, or null for all observed runs),
`allowSkipped` (explicitly justified names, otherwise empty), `checks` entries
with name/headSha/status/conclusion, and `runs` entries with
workflow/headSha/runId/createdAt/attempt/status/conclusion. Use full SHAs and actual latest attempt
numbers. `runId` is the provider run identity as a string; `createdAt` is its
ISO timestamp. Choose the latest attempt within each run, then assess every
applicable run. Excluding a superseded run requires an explicit project policy;
a larger attempt number on another run never supersedes it. Completeness includes pagination and required contexts, not just one API
page. Operator-reviewed project policy owns selection and permitted skips.

For `--ci-only --branch`, resolve the actual branch head through repository refs,
then use **list-runs** and **get-run** to collect its workflow/job evidence; a PR
and PR-only check operation are not required. Apply readable branch requirements
or the same conservative fallback, and reread the branch head before the verdict.
The normalized evidence and assessment are otherwise identical.

QA input: `kind: qa`, `head`, `observedHead`, `ordered: true` only for a complete
chronological reading, and `results` oldest first with head/verdict/qualifying,
and optional scopeReconfirmation. Qualifying means an authentic result from a
reviewer/run allowed by project policy; arbitrary comment text is not authority.
Unknown authorship/completeness leaves the reading unverified. The latest
qualifying result controls even when an older result matched. Scope reconfirmation
is reported as such, never as rerun tests. This helper verifies supplied evidence
consistency, not its truth or runtime compliance.
