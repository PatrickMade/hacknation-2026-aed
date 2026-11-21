# Retain a report before publication

Use this procedure in report preparation for every provider, including OpenAI,
Codex and Claude. Missing upload access never skips local preparation. Apply
inspect and explicit metrics disablement first. Preserve legacy report files;
use the helper for new revisions rather than silently moving old evidence.

## Prepare one revision

1. Finish task-scoped extraction and arithmetic under the report contract.
   Prepare a normalised local report containing `schema_version: 1`, the bound
   `run_id`, stable `task_ref` and nullable `metrics`. Keep provenance/coverage
   and requested versus confirmed execution settings in that report. Preserve
   available observations when remote identity is missing. Exclude credentials,
   raw transcripts and secret values from every input/artifact.
2. Resolve the installed `scripts/local-report.mjs` and the invoking Git project.
   Put JSON on private stdin or in a private input file; never pass report bodies,
   credentials or source content in argv. For `prepare`, supply:

   ```json
   {
     "revision": 1,
     "report": {"schema_version": 1, "run_id": "run_example", "task_ref": "local:run_example", "metrics": {"calendar_ms": null, "delivery_ms": null}},
     "payload": null,
     "destination_id": null,
     "reason": "missing_binding"
   }
   ```

   Replace example identity with the verified task/run. When transport is bound,
   supply the minimised payload and its approved opaque `destination_id`; its
   remote revision must match this revision. The helper checks basic identity
   and metrics, but **does not validate the full remote schema or grant upload
   authority**. Native transport/schema validation is still required before
   submitting. Keep that validation's source id in the ledger.
3. Invoke the helper before any external call and before cleanup:

   ```bash
   node "$LOCAL_REPORT_HELPER" --project "$PROJECT_ROOT" --run-id "$RUN_ID" --task-ref "$TASK_METRICS_REF" --operation prepare < "$REPORT_INPUT"
   ```

   It writes a single private `report-<revision>.json` bundle under the same
   clone-common `task-metrics/<RUN_ID>/` directory as capture. The bundle keeps
   report, canonical payload (or null), their hashes and publication state
   together. Save its returned `artifact_path` in the local run context and
   read it back. It survives linked-worktree cleanup. Same revision/content
   returns the existing state; changed evidence/payload uses a new revision,
   retaining all prior bundles. Reuse the same opaque report key when available.
4. Supply `--local` only for explicit local-only intent. It records `local_only`
   and blocks publication transitions for that revision. A later authorised
   publication creates a new revision without altering the local-only record.
   `--inspect` writes nothing; a missing or false `metrics.enabled` is `disabled`.
   If Node/Git/helper or private writable storage is unavailable, state the
   reporting gap and preserve already-existing evidence; do not widen access,
   install software, invent a path or claim the report was saved.

## Record bounded transport results

Use the same helper/options and `--operation` below with JSON on stdin. The
helper makes **no network calls**. Actual native operations and receipt
provenance are owned by the authorised transport procedure.

| Operation | Input and effect |
| --- | --- |
| `read` | `revision`; returns state, bundle pointer, canonical hash and next action |
| `attempt` | `revision`, opaque `validation_source_id`; records uncertainty **before** one native submit; refuses a blind second attempt |
| `pending` | `revision`, controlled `reason`; preserves report/payload and uncertain-write evidence; optional bounded `http_operation`, `http_status`, `error_code`, or local `validation_error`/`validation_path` |
| `receipt` | `revision`, `source_id`, matching `receipt`; records `stored` only on exact destination, project/task/report key/revision and `canonicalSHA256` |
| `not-found` | `revision`, `source_id`, exact `lookup` identity and `after_submit_attempt`; records a freshly verified not-found result for that same attempt before a later retry |

`receipt` has only `destination_id`, `project_id`, `task_id`, `report_key`,
`revision`, `canonicalSHA256`. `lookup` has the same fields. Use the actual
native receipt and a source id mapped to its task-scoped readback in the ledger;
ACK, queued response or HTTP200 is insufficient. Never manufacture receipt or
not-found evidence. A stale not-found result cannot authorise another submit.

Pending reasons are `awaiting_submission`, `missing_binding`,
`access_unavailable`, `tools_unavailable`, `offline`, `submission_failed`,
`readback_unavailable`, `uncertain_write`, `conflicting_receipt`, `invalid_payload`,
`report_too_large`. HTTP diagnostics accept only `reports`/`receipts`, integer
status 100-599 and the fixed codes `report_too_large`, `invalid_request`,
`access_denied`, `revision_conflict`, `receipt_not_found`, `operation_unavailable`.
Never pass arbitrary server messages, headers, credentials or body text. Keep detailed
non-secret explanations in the local ledger, outside remote payloads.

For `invalid_payload`, local diagnostics accept only these exact code/path pairs:

- `validation_error: end_before_start` with `validation_path` shaped as
  `<section>[<index>].end`. Sections are `attempts`, `intervals`, `rounds`,
  `usage.requests` and `cost.applied_rates`.
- `validation_error: unknown_actor` with `validation_path` shaped as
  `intervals[<index>].actor_id`, for an actor/reference or scope violation.

The index is a canonical non-negative decimal with at most four digits. Both
fields are required together. Never put input values, timestamps, actor/source
identifiers or raw error text in these fields. Validation leaves the retained
payload, identity, hash and submission history intact; it does not repair input.

If a call fails, use `pending` with its cause when local storage remains usable.
Reconcile an uncertain native write once by receipt readback; keep pending if
unresolved. Do not submit again in the same reporting invocation. On a later
explicit invocation, reconcile first; only the verified same-identity not-found
result and the existing idempotency contract permit a retry in transports whose
contract allows it. The direct GitHub helper reconciles receipts only after any
prior submission attempt; it never submits that revision again. No background job
or repeated polling is installed. Stored revisions are never reset or resent.
The caller's original task outcome and QA verdict are preserved throughout.

## Interrupted local writes

Mutating operations reserve `report.lock` exclusively and record the helper's
owner PID and creation time. A live writer keeps that reservation; never delete
it to force a second writer. Atomic `read` remains available without the lock
and changes no files, so inspect the retained identity/hash/submission state
first. A PID alone is not proof of ownership because process ids can be reused.

If the helper was interrupted, reconcile the exact task-owned invocation with
the host's supported process/session metadata. Only after proving that owner
exited and that no helper for this run is writing may the owning agent remove
that one private stale lock. Empty/ambiguous lock or missing ownership evidence
requires owner intervention; never scan unrelated process arguments or
environments. Then re-read the same revision, preserve its hashes and attempts,
and follow receipt-first recovery. The helper never steals or automatically
expires locks. Failure leaves a named local-storage gap and preserves delivery.
