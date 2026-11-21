# OpenAI and Codex execution evidence

Use during evidence intake when an executor runs an OpenAI model through Codex
or a supported T3 OpenAI provider. Reuse the same reporter, time contract and
transport as other providers; a new model is not a new task or reporter.

## Capture on the executing surface

The installed delivery/continuation caller invokes checkpoint capture at start,
phase/wait transitions and frozen exit, then invokes this reporter. This works
through skill execution, not an assumed OS/provider stop hook. Do not install
hooks, modify global configuration or launch a CLI relay to make it automatic.
Unexpected termination leaves an unclosed observation; continuation records the
unknown gap and reconciles actual native evidence. Metrics failure cannot hide
the original task failure.

For T3, discover the native read tools on the current host. Use `t3_thread_read`
for the exact task-linked thread and bounded run metadata; use `task_status`
only for actual owned delegated task ids already in the caller's inventory.
Do not create a thread/worker to obtain metrics. Record the tool/version,
thread/run/attempt linkage and read time in the private source ledger.

- `recentRuns.requestedAt`, `startedAt`, `completedAt` and status are run
  observations, not whole-task delivery boundaries. Keep native request,
  actual start, first observed preflight, claim and ledger creation separate.
  First contemporaneously observed preflight remains the forecast comparison
  start when that is the frozen contract. Missing values stay null.
- `reuseEvidence.requestedModelSelection` describes requested model/options.
  A thread's current model or `recentRuns.model` alone does not establish the
  actually executed historical model/effort. Confirm only from execution
  metadata with explicit semantics; otherwise leave confirmed fields null.
  Preserve each retry/provider recovery as its own linked attempt.
- A completed provider turn can have working children. `task_status.workState`
  and `hasPendingChildRuns` qualify task completion; an ACK or completed main
  run never proves the final delivery. Use the caller's actual acceptance and
  frozen boundary, and record inaccessible children as missing coverage.
- The available lifecycle tool may expose no tokens or costs. Use only actual
  provider counters with request identity and confirmed subset semantics.
  Cached input is part of input; reasoning tokens can be part of output.
  Never infer usage from text, context snapshots or model capability.
- Cross-host clocks, parent/child overlaps, unobserved intervals and actor-level
  waits retain the existing contract's uncertainty. Only the documented UNION
  of whole-task human block/suspension is deductible; tests/builds/CI remain
  delivery. Provider limits alone do not prove every actor stopped.

When these tools are unavailable, use the caller's exact local checkpoints and
approved task-scoped source artifacts with explicit partial coverage. Never
scrape unrelated histories, persistent memories, process arguments/environments
or credentials. An input source claiming a task identity is not proof: require
the native task/thread linkage supplied by the owning caller/readback.

## Finish even without transport

Prepare the normalised report under `references/local-retention.md` before any
publication decision. Missing credentials, service access, binding or native
submit/readback tools leaves available measurements local and publication
pending. Use the existing authorised native transport only when actually
available. The local helper stores evidence and hashes; it neither calls AWS
nor logs in. Its installed presence is not live provider or cloud acceptance.

Acceptance needs one real OpenAI/Codex task's caller/checkpoint invocation,
source-backed report, exact stored receipt and estimator read of the same report.
A local offline canary can prove retention only. Keep these states separate.
