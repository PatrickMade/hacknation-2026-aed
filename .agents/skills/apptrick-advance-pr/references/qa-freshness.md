# QA freshness

Before reporting QA as current, read the PR head and the latest qualifying QA
result or explicit scope-reconfirmation, including complete ordered comments.
Match its tested SHA to the current head. Missing SHA or unavailable/ambiguous
ordering means unverified; a mismatch means stale. Never prefer an older matching
comment over newer contradictory evidence. A fresh scope-reconfirmation states
its scope and current SHA; it is not a claim that tests were rerun.

Follow project policy for required QA and merge authority, including when labels
are disabled. Do not add a second-reviewer or manual evidence-block gate a project
has withdrawn. A legacy sign-off without SHA remains visible but cannot be called
current. User permission to merge does not turn stale evidence into a test PASS.
Re-read the head before the authorized merge and reassess after a change.

## Executable assessment

Use this skill's own `scripts/assess-verification.mjs` with `kind: qa` and
the normalized input described in [CI completeness](ci-completeness.md).
Require `status: pass`; exit zero alone only confirms readable input. Retain
the result, assessed SHA and source evidence. Do not fabricate completeness
or qualifying authorship. The helper checks consistency, not authenticity.
