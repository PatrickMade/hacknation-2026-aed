# Direct reports using existing GitHub access

Use only for an operator-approved `direct_github` transport. This lane requires
no separate metrics account, MCP login or CI runner. It uses the executing
developer's existing GitHub CLI credential to verify active organisation
membership and write access to one approved repo. Each remote operation
rechecks access; package installation never grants authority.

## Approval and local preparation

Before using this lane, require explicit operator/developer approval to forward
the current caller's existing GitHub token ONLY to the designated company HTTPS
metrics backend. This is an additional credential recipient, not permission
implied by a repository checkout or a token's existence. Do not share another
user's token or install/configure/login to gh automatically. The backend does
not store the token or create a developer account; the token stays in process
memory during the TLS request and fixed GitHub API verification calls.

The private operator-owned descriptor (`0600`, regular, non-symlink) has
`kind: direct_github`, `enabled: true`, `credential_forwarding_approved: true`,
approved `endpoint`, opaque `destination_id` and `project_id`. The endpoint is
the exact deployed AWS HTTPS execute-api host and stage, never supplied by the
report/task. Consent recorded in a descriptor is valid only when backed by the
operator's actual approval. There is no endpoint or credential in this package.

1. Prepare/read back a local revision under `references/local-retention.md`.
   Keep the task result, source ledger, opaque identity and canonical hash.
   Missing remote binding leaves payload null and local pending. When bound,
   construct only the minimised payload; credentials/raw sources never enter it.
2. Verify the backend actually implements the approved project/repository/owner
   binding, membership/permission checks, strict schema and receipt semantics.
   Resolve this skill's installed `scripts/direct-github-publish.mjs`.
3. Create fresh opaque source ids for this invocation's receipt evidence and
   prior payload validation, mapped in the private ledger. Invoke through a
   supported deterministic command; all report/credential content stays out of
   argv. Only paths and opaque references are arguments:

   ```bash
   node "$DIRECT_REPORT_HELPER" --project "$PROJECT_ROOT" --run-id "$RUN_ID" --task-ref "$TASK_METRICS_REF" --revision "$REVISION" --transport "$APPROVED_DESCRIPTOR" --source-id "$RECEIPT_SOURCE_ID" --validation-source-id "$VALIDATION_SOURCE_ID"
   ```

   The helper reads the retained bundle. Its shipped structural/privacy schema
   rejects extra/private nested fields before retrieving any token. The remote
   service still owns semantic/source validation. Schema model vocabulary is
   pinned: an unsupported model leaves pending until all consumers are upgraded;
   never relabel a model to fit the schema.
4. The helper resolves `github.requiredaccount` through Git configuration in
   `--project`, not the caller's working directory. When declared, it invokes
   the GitHub CLI token lookup with `--hostname github.com --user <account>` only,
   with ambient GitHub token variables removed from the credential subprocess.
   A missing login or invalid account/configuration leaves `access_unavailable`;
   it never falls back to the globally active account or invokes login/switch.
   The failing account-specific command yields no usable token. When no account
   is declared, the existing active github.com account behavior is retained for
   compatibility; operators must approve that caller's credential forwarding.
   All credential retrieval stays within its process;
   stdout containing the token is never forwarded to the agent, logged or saved.
   The credential subprocess has a finite 15-second budget to accommodate an
   existing account guard. An over-budget lookup stays `pending/access_unavailable`
   with only `credential_error: credential_timeout` in its private publication
   observation. Missing credentials retain the same reason without that subtype;
   child errors, stdout and stderr are never retained. Do not bypass the guard,
   switch accounts or refresh credentials to force publication.
   It invokes no login. It validates the descriptor, enforces certificate and
   hostname verification, and refuses disabled TLS checks or credential-bearing
   Node diagnostics before token retrieval. It uses no proxy/redirects and bounds responses and publishes at most once after exact
   receipt-not-found. A retained revision with a prior submit attempt is only
   reconciled by receipt lookup, never submitted again. Before submit it records uncertainty locally. A timed-out
   or 5xx submit gets one receipt read; an unresolved result stays pending.
5. Require exact stored receipt all4/hash and the approved destination. A matching
   receipt marks the same local revision stored without re-sending. HTTP200,
   queued work or an ACK is insufficient. Inspect/local/disabled intent makes
   no auth/network calls. Never resend an unchanged stored revision.

## Missing access and limits

No gh installation/session, missing token scope, inactive membership, absent
repo write access, disabled endpoint, API rate limit/network/readback failure
retains local pending with a reason. Do not make a new key, overwrite a stored
revision, invoke login or copy credentials to force success. A later explicitly
invoked report run reconciles the same identity first. Keep exact retry artifact.

The developer needs existing GitHub access and an approved token-forwarding
policy; this does not promise uploads from an unconfigured anonymous computer.
Permission to submit does not grant calibration/list access. Approved repo
writers can self-report observations, so qualify timing/usage/source coverage
before using reports in estimates. Native estimator read of the stored report
remains a separate acceptance gate. Publishing failure never changes task QA.

## Payload limits and safe diagnostics

The service request boundary permits at most 262144 UTF-8 bytes. Report validation
reserves 16384 bytes for the storage envelope, so the compact canonical JSON
payload must be at most **245760 bytes (240 KiB)**. The shipped validator checks
this before credentials/network and leaves `pending/report_too_large` on failure.
It also rejects duplicate `attempt_id`, `interval_id` and `round_id` within their
respective arrays as `pending/invalid_payload`. Schema array limits still apply:
1024 run ids, 2048 sources/attempts/intervals/rounds, 4096 usage requests, 64 source
ids per row and 128 applied cost rates. Local validation also checks that
`coverage.covered_sources` equals the unique `source_ids` count, the covered and
missing sets are disjoint, a non-null `missing_sources` equals the unique
`missing_source_ids` count, and `expected_sources` equals covered plus missing
when both expected and missing counts are non-null. Inconsistency leaves
`pending/invalid_payload` before credentials/network. These fields count source
identities, not observations, intervals or attempts. Preserve null for unknown
counts; never replace unknown with zero or invent source IDs to match a counter.
Local validation also rejects a row whose non-null `end` precedes its `start`,
using the full UTC microsecond precision. Equal instants and allowed null ends
remain valid. It inspects attempts, intervals, rounds, usage requests and applied
rates like the service; the current schema gives start/end only to attempts and
intervals. Do not add time fields to the other categories. Rejection leaves
`pending/invalid_payload` before credentials/network, with fixed
`validation_error: end_before_start` and a safe `validation_path` such as
`attempts[0].end` in the private publication observation. The diagnostic contains
no timestamp, identifier or source content; use the retained local sources to
diagnose the producer without altering the frozen report.
Local validation also requires every actor-scope interval to name an actor in
`attempts[].actor_id` of the same payload, and every task-scope interval to have
`actor_id: null`. An orphan actor, actor/null or task/non-null mismatch leaves
`pending/invalid_payload` before credentials/network with only the fixed pair
`validation_error: unknown_actor` and `validation_path: intervals[<index>].actor_id`
in its private observation. The index is a canonical non-negative decimal with
at most four digits. It contains no actor value or source content. The helper
does not drop, null, re-scope or otherwise repair intervals/attempts; retain
unpublishable actor intervals locally and account for their sources as missing
when evidence supports a future payload. Never rewrite or replay a historical
revision to satisfy the rule, or infer that this identifies an earlier HTTP 400.
The backend additionally checks row source references and semantic consistency; local
validation alone is not service acceptance.

Failed HTTP calls retain only `http_operation` (`reports` or `receipts`), integer
`http_status`, and an optional fixed allowlisted `error_code` in private
publication observations. Allowed codes: `report_too_large`, `invalid_request`,
`access_denied`, `revision_conflict`, `receipt_not_found`, `operation_unavailable`.
Unknown strings, headers and response bodies are never retained or printed.
Empty/non-JSON error responses retain their HTTP status without body text.
An observed HTTP status does not prove the underlying cause: the service can
return 400/`invalid_request` for schema, source-reference or semantic rejection,
including duplicate interval identifiers. Payload size alone cannot diagnose it.

For an incomplete source inventory, do not lower a claimed total solely to pass
validation or substitute a count of missing observations for missing source
identities. Reconcile the producer's inventory and counters; if a count remains
unknown, use the schema's null value and preserve source evidence locally.

Preserve rejected revisions and their original bytes/hash. The producer owns
source reconciliation and a corrected **new revision**. Do not silently deduplicate,
truncate or split a frozen report, or invent missing measurements. A split upload
would need an agreed service/estimator contract. Receipt-first reads may recover
an already stored revision, but cannot authorise a second direct submit of the
unchanged payload, including after a 4xx, timeout or unresolved 5xx.
