# Task metrics report contract

Use this contract in steps 2-4 for source extraction, calculations and artifacts.

## Identity and artifacts

Use schema version `1`. Keep local `RUN_ID` and native task linkage in the ledger;
use opaque project/task identifiers bound by the approved transport for remote
records. One task can contain multiple logical runs; aggregate only explicit
task-linked runs and retain the run inventory so a resume is not a second task.

Persist a task-owned metrics directory under `<paths.runs>/.metrics/<RUN_ID>/`
only when its runtime contents are ignored and outside managed skill files.
Otherwise use an authorised ignored runtime location and record it in the
handoff; never change ignore rules or configuration from this skill. Save:

- `ledger.json`: local source map, original counters, extraction limitations
  and calculation evidence. Keep source content in its existing artifacts.
- `report.json`: normalised observations and derived metrics.
- `payload.json`: the publication allowlist below, without the local source map.
- `publication.json`: target binding, revision, payload hash, status, attempts
  and verified receipt. Keep credentials out of every artifact.

Write artifacts atomically with a deterministic tool and preserve existing
revisions. Invalid input produces a named analysis failure, never a valid-looking
zero report. Reuse an unchanged report/revision; changed evidence or
classification creates a new revision without overwriting the prior payload.

For the shipped delivery integration, use the checkpoint helper's private run
directory in the clone's Git common directory as the authorised runtime location.
Keep ledger/report/payload/publication revisions there alongside lifecycle.json;
pass its pointer in the local run context, never a public comment. For new
revisions use `references/local-retention.md` and its single atomic revision
bundle; it contains report, optional payload and publication state together.
Legacy separate files above remain valid and are never silently overwritten.
This keeps evidence outside commits and preserves it through linked-worktree cleanup.
Legacy ignored runtime locations remain valid; do not move/delete old artifacts
or change their identity. A ready PR freezes `partial_checkpoint`, not
`verified_delivery`.

## Publication allowlist

The payload contains only these top-level fields; reject additional fields:

| Field | Content |
| --- | --- |
| `schema_version` | `1` |
| `report_key`, `revision` | Stable opaque report key and positive revision |
| `project_id`, `task_id`, `run_ids` | Approved opaque bindings and run inventory |
| `boundary` | `verified_delivery` or an explicitly partial checkpoint |
| `outcome` | `completed`, `blocked`, `aborted`, `partial`, or `no_action` |
| `classification` | Controlled task type, stack/reuse tags and sourced scope-change category; no private narrative |
| `coverage` | Expected/covered/missing/duplicate counts, opaque missing source ids and completeness per metric |
| `attempts` | Opaque actor/attempt ids, role, model and reasoning observations with source ids |
| `intervals` | Timestamped phase/state observations, actor linkage and measurement basis |
| `rounds` | Review/gate/browser/QA/E2E round id, candidate SHA, result and source ids |
| `usage` | Deduplicated request usage, disjoint billing buckets, units, model and source ids |
| `metrics` | Nullable elapsed delivery, actor activity, technical waits, human-block and suspension quantities in milliseconds |
| `cost` | API-equivalent totals/known subtotals, completeness, currency, pricing revision and applied rates |
| `estimation_ref`, `reporting_overhead` | Optional opaque baseline reference and separate reporting usage/time |

Nested values also follow the definitions below. Allow only controlled enums,
opaque identifiers, validated timestamps, candidate hashes, public model/stack
names, nonnegative numbers and pricing metadata; reject arbitrary free text,
URLs, local paths, commands or embedded documents. Keep human-facing
explanations local. A hash is an integrity identifier, not anonymisation of
private names; use approved opaque bindings instead.

Every observation carries opaque `source_ids` and a basis of `observed`,
`reconstructed`, or `unavailable`. Unavailable quantities are null, never zero.
State known partial quantities as subtotals, not task totals. Missing inventory
or unclosed intervals prevent a claim of exact whole-task coverage.

Every non-null `intervals[].actor_id` must name an `attempts[].actor_id` in the
same payload. `scope: actor` requires a non-null referenced actor; `scope: task`
requires `actor_id: null`. Multiple attempts may name the same actor.

If evidence cannot support an actor's attempt, retain its intervals in the local
bundle and account truthfully for their sources as missing in a future payload.
Never repair an actor interval by nulling its actor, re-scoping it to task, or
borrowing another actor or start. Do not derive attempt timestamps to satisfy
this rule. The validator refuses inconsistent input without normalizing it;
payload-only validation cannot prove the original bundle lineage. Historical
reports, identities, boundaries and publication state remain unchanged.

## Time and concurrency

Keep UTC start/end observations and available monotonic duration/clock-session
evidence locally. Reject reversed, nonfinite or contradictory intervals;
cross-host alignment requires known clock uncertainty. Do not subtract monotonic
readings from different processes or clock sessions. Without adequate clock
evidence mark the derived duration reconstructed or unavailable.

Use half-open intervals `[start, end)`. Phase names are intake, diagnosis,
specification, planning, implementation, correction, validation, review,
browser, qa, e2e and finalisation. States are active, technical_wait,
human_block, suspended and unknown. State observations declare whether they
apply to one actor or the whole task; an actor waiting does not block the task
while another linked actor continues work.

- `calendar_ms`: observed completion boundary minus observed task start.
- `delivery_ms`: calendar interval minus the union of proven whole-task
  human blocks and suspension, including required builds, CI, tests and
  technical waits. Derive only with complete lifecycle/state coverage; uncertain
  gaps stay unknown rather than becoming active agent work.
- `actor_activity_ms`: union of proven direct active intervals for each actor,
  summed across actors. Exclude inclusive parent/container spans and coordinator
  waits; count actual direct coordinator activity once.
- Phase activity: apply the same per-actor union within each phase. Resolve
  conflicting phase assignment from evidence or leave the affected breakdown
  unknown. Do not add nested phase/round elapsed spans into a task duration.
- Wait totals: report interval unions and distinguish actor-level waits from
  whole-task delaying waits. Overlapping waits are not additive components of
  `calendar_ms`; expose overlap rather than forcing a misleading decomposition.

Freeze the delivery boundary before this skill's analysis. Record its own cost
and time as reporting overhead. Do not measure or estimate human labour; a human
response delay is a task state, not human effort. Never divide a task or project
total by the configured number of agents.

## Usage and pricing

For each request retain provider identity, model confirmed by execution when
available, requested model/settings separately, reasoning setting and its
provenance, and whether usage is final or still pending. Preserve provider-native
reasoning labels; they are not equivalent compute budgets across providers.

Deduplicate by provider/request identity and explicit cross-source linkage.
If requests lack reliable identity, expose possible duplicates and keep whole
task usage partial. Distinct billed retries count; a repeated observation of one
request does not. For cumulative counters, take verified final totals or valid
deltas within a known counter scope; account for resets and overlapping actor
rollups. Do not sum snapshots. Capture the entire executing task, including
failed attempts and required review/QA, when accessible.

Keep original usage locally, then map into provider-specific **disjoint**
billable buckets. Cached input can be a subset of total input; reasoning can be
a subset of output. Never add either twice. Distinguish cache reads/writes and
their TTL/rate where the provider bills them differently. Tool-response text is
not extra usage when already counted by the provider. Do not infer usage from
character counts or report an absent bucket as zero.

Obtain rates from an authorised pricing snapshot with source URL, effective
date/revision, currency, model, tier, context bracket/cache policy when relevant,
bucket and unit. Validate nonnegative finite counts and rates. Compute
`sum(bucket_count * rate_per_unit)` with deterministic decimal arithmetic;
round only displayed totals. Sum only compatible currencies. Unknown usage or
rates yield an explicit known subtotal and null full total. A known zero requires
positive evidence of zero usage/rate, not missing data.

Label the result `api_equivalent`, not actual subscription spend. Keep requested
and historical pricing bases distinguishable; repricing creates a new version.
Assign shared orchestration usage once with an explicit allocation source or
keep it unallocated. Late final counters make usage pending until a later
authorised analysis can obtain them; do not recursively analyse reporting.
