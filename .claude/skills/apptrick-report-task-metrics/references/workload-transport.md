# Approved workload transport without developer login

Use only when the operator-approved transport descriptor names a verified
workload/runner binding rather than an individual-login MCP transport. Read
this procedure from `references/transport.md`; it does not install a runner,
create a role, grant access or enable workflows.

## Preconditions

The operator binds the exact destination/project, approved workload identity,
actual submit/receipt operations, payload schema, pinned client artifact and
receipt contract. The workload obtains short-lived credentials outside model
context. A project-approved CI/OIDC or managed-host identity may replace
individual developer accounts; an installed skill or project id in a report
never proves authority. Preserve existing verified transport routes.

A developer using this lane needs no separate metrics account or MCP login.
They still need access to the project's approved execution/submission channel.
For a local workstation task, require a supported authorised transfer of only
the validated minimised payload to the runner and the exact receipt back to its
owner. If that channel is missing, retain local pending; do not upload through
an invented workflow, commit runtime reports, transfer private ledgers, create
shared tokens or change GitHub/AWS/global settings. Tasks executed within an
already-approved workload may use its actual bound client directly.

## Execute and recover

1. Prepare and read back the local revision under `references/local-retention.md`
   before any remote operation. Validate/minimise against the actual destination
   schema; keep identity/revision/hash and original task result unchanged.
2. Verify the actual runner/client binding and its project scope. It may submit
   and reconcile receipts only; calibration/list reads require separate analyst
   authority. A workload identity attests the caller, not elapsed completeness
   or the accuracy of self-reported measurements.
3. Record the submission attempt in private local state before invoking a bound
   publisher. The client reconciles the exact identity/hash before submitting,
   performs at most one submit and one post-submit receipt read, and never logs
   temporary credentials, signed headers, raw source or report contents.
4. Require a durable stored receipt matching all four identity fields and the
   canonical hash at the approved destination. Normalize a service-provided
   `payload_sha256` to the local helper's `canonicalSHA256` only after checking
   the actual contract. Do not accept a queued job, HTTP200, upload artifact or
   completed workflow as proof of report storage.
5. Missing workload credentials, channel, runner, network or receipt retains
   local `pending` with cause and exact retry artifact. The next authorised
   invocation reconciles before any resubmit. Never fall back to a developer's
   secret store or interactive login merely to force this lane to succeed.

Keep source readiness, runner authentication, exact report storage and native
estimator read as separate acceptance states. Leave unavailable capabilities
explicit. The reporter creates no background job, recurring retry or new task.
