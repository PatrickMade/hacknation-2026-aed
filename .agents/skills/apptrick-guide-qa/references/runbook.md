# Runbook generation

Write sanitized `runbook.json` and run this skill's
`node scripts/render-runbook.mjs runbook.json runbook.html`.

Input has exactly `runId`, full `headSha`, `scenarioId`, `title`, and `cases`.
Each case has `id`, `title`, `steps` (strings), `expected`, `status`
(`not-run`, `pass`, `fail`, `blocked`), optional `observed`, and optional `evidence`
(relative `screenshots/*.png|jpg|jpeg` paths inside the artifact folder). No login
fields, tokens or passwords. Reference the project's secure authentication flow
outside the artifact. Never use real customer data as an example.

Generate once before execution with all cases not-run. Regenerate the same file
with actual AI results afterward; retain the revision, run and scenario identity.
Case storage keys include their immutable definition, so changed expectations
cannot inherit an old human pass. A different revision/run requires a new output
path and is not allowed to overwrite prior evidence. Keep archived runbooks.

The renderer escapes display values, embeds only safe JSON in its data block,
and uses DOM text values and registered event listeners. Do not replace it with
string interpolation of tracker content into scripts or event handlers. Reject
unsafe artifact paths and symlinked screenshot sources before publication.

Open the HTML through the available browser and test human Pass/Fail/Skip,
refresh persistence, early-to-final update, changed-case reset, and storage-disabled
fallback. If this cannot be exercised, distinguish generator tests from browser
verification. No external hosting, upload or shared URL is implied by a local file.
