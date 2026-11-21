# Capture one local lifecycle observation

Use only for `--checkpoint`. Honour inspect mode before any event/context write;
capture runs only when `metrics.enabled` is `true`. A missing or false key means
capture disabled; explicit enablement is still not permission to upload.

1. Bind the canonical task and stable `RUN_ID` from the caller's verified local
   context. Persist `TASK_METRICS_REF` once: use the canonical native task reference
   when one exists; for an allowed issue-less brief use `local:<RUN_ID>`. For an
   adopted PR without prior context use its canonical repository/PR identity.
   Reuse this value on every later checkpoint, including after a PR opens or a
   task is linked; new linkage supplements it rather than replacing it. Never
   force creation of an issue to enable local capture. Remote opaque binding and
   its provenance remain separate publication requirements.
   Keep opaque actor and provider-attempt identifiers in that context;
   a changed provider session starts another attempt, not another task/run.
   Requested and runtime-confirmed model/effort belong to separate evidence.
2. Resolve the installed helper at this skill's own `scripts/checkpoint.mjs`
   and the invoking Git project root. Use Node.js and Git if available; do not
   install dependencies or substitute a network collector. Without the helper,
   return a concrete measurement gap and continue the caller's delivery.
3. Create a private input artifact with an opaque `event_id` and keep it for
   retries. Supply only `event_id`, `type`, `actor_id`, `attempt_id`, `phase`,
   `state`; `close` also requires `outcome` and `boundary`. Use enums from the
   report contract. Derive task identity from readback, never from event content.
   Record a phase before its work/tool call and after its result; capture actual
   wait entry/exit when known. Default state is `unknown`. An orchestrator waiting
   for children does not establish a whole-task human block or suspension.
   Apply [wait classification](wait-classification.md) to observed human,
   suspension and technical-wait transitions; retain unobserved gaps.
4. Run the helper using an argv-safe tool, or correctly quoted variables:

   ```bash
   node "$CHECKPOINT_HELPER" --project "$PROJECT_ROOT" --run-id "$RUN_ID" --task-ref "$TASK_METRICS_REF" < "$EVENT_PATH"
   ```

   The helper writes UTC observations atomically, with private permissions,
   under the executing clone's Git common directory at
   `task-metrics/<RUN_ID>/lifecycle.json`. No network, credentials, hooks or
   usage extraction run. Keep the returned `ledger_path` in the local context.
   It survives linked-worktree cleanup and is never staged. Restrict the event
   input and all reporter artifacts to the same private run directory. When
   storage cannot prove privacy, retain a named gap rather than widening access.
5. Reuse the same event id/bytes after an uncertain local result. Conflicting
   identity/event input or a residual `checkpoint.lock` stops capture, never
   resets the ledger. Reconcile the owned process before removing a stale lock;
   do not treat it as permission to steal another writer. `resume` retains all
   prior observations and explicitly marks an unknown gap. A new/resumed actor
   does not invent a missing beginning. `close` freezes a checkpoint; subsequent
   work requires `resume`, preserving the previous close in history.
6. Return `recorded`, `unchanged`, `disabled`, `not_written` or a concrete gap,
   the ledger pointer and event count. This is capture evidence, not a report
   receipt or proof of full measurement coverage.

The helper intentionally leaves all report metrics null. Its clock is wall time,
with unverified alignment; analyse clock provenance and actual state/lifecycle
coverage before deriving durations. Whole-task start can precede run binding.
Report the observed span as a partial/reconstructed quantity when appropriate.
Actor activity and provider tokens require their own actual sources. Keep gaps,
attempt overlaps and inaccessible children explicit; never sum phase checkpoints
as active time. Unexpected termination has no synthetic end event. A continuation
records the gap and reconciles available native evidence.

Cross-clone/host continuation transfers minimised ledger/report/publication bytes
through the approved task handoff, with hashes and the same opaque identity.
Keep the existing files locally; verify the received task/run identity before
placing them in private runtime storage. A merged event id with different bytes
is a conflict. Never transfer tokens, raw transcripts or local source passages.
If the previous ledger cannot be recovered, begin with `resume` and an explicit
missing-history gap; do not reset the task's measured start or invent duration.
