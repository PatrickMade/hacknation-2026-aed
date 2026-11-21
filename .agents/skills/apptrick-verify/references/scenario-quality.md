# Scenario and evidence quality

Before running, bind the scenario to the actual checked-out revision and record
repository, head SHA, run id and scenario identity. For multi-repository behavior,
record each tested revision. A remote PR head alone does not prove which code ran.

For changed UI, include required cases for relevant default, empty, loading,
error, no-permission, long-content and narrow-viewport states. Explain genuinely
inapplicable states; missing required behavior is FAIL, not an informational note.
When `.uxproof/` exists, check applicable tokens, registered components and screen
contracts. A neutral discovery prototype is a flow hypothesis, not a visual spec.
Read the manual section of `.uxproof/conventions.md` before judging generated
rules; it wins on conflict. Advisory or unconfirmed palette/component choices
are questions, not product violations or blocking findings. Independent observed
usability or accessibility defects still follow the normal evidence rules.
Drive the product UI; Swagger or a login screen alone does not test the feature.

Capture decision-relevant screenshots and optional before/after-action evidence
when project policy requires it. Respect the configured headed/headless mode and
session ownership; never close other runs' browsers. Inspect every included image
after the scenario for broken layout, errors, missing labels and unintended data.
Record each finding with its image as introduced defect, improvement or
pre-existing issue; say explicitly when the review found none. A captured file
without visual inspection is not a completed screenshot review.

When claiming headed/headless execution, bind the observed mode to this run's
session using supported provider metadata or verified process ancestry. Finding
any Chrome process, or passing a launch flag alone, is not proof. Do not inspect
or close another session, dump process arguments, or steal focus to obtain it;
when ownership/mode evidence is unavailable, report that limit. Resolve screenshot
destinations to absolute paths in this run's artifact directory (or verify the
provider-returned artifact), confirm the file exists and is non-empty, then open
it for review. A successful screenshot command alone does not prove the expected
file was saved. Keep unattended runs in their configured mode; this check does
not require launching a visible window.

Use synthetic or approved isolated test data. Never put passwords, tokens or
customer data in reports, screenshots or publishable runbooks. Omit/redact unsafe
evidence and state the missing coverage. Publish only within the authorized
tracker/audience. Evidence paths must be unique to head and run; never overwrite
an older run's screenshots. Read back the posted comment and actual image access;
local file paths are not a remotely accessible attachment.

A self-QA sign-off is forbidden for risk-high changes, whether risk follows a
label or the diff: a diff that widens access control (authorization, sessions, grants, tenant or scope filters), rewrites or deletes existing data or changes a migration runner, changes how money is computed or moved, changes module boundaries or state ownership, or breaks a published contract → `risk-high` (only tightening access, an additive migration with up/down evidence, display-only amount changes and stricter validation of invalid input are not high-risk on that ground; unclear direction counts as high-risk). The project's `SDLC.md` holds the full table. Post evidence and leave sign-off to the project's reviewer policy.
For an authorized lower-risk sign-off, include `QA head: <tested-sha>` and the
scenario, environment, data, negative cases and result. A partial run never
becomes PASS or approval. Labels-disabled projects record the evidence without
inventing labels, a second-reviewer requirement or a manual password-like comment.
