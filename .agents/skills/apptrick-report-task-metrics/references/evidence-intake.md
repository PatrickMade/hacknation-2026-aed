# Evidence for one task

Use this procedure in steps 1-2 to establish coverage before deriving metrics.

1. Read `<paths.runs>/.sessions/<RUN_ID>.json` and the caller's existing
   plan/run-folder/handoff when available. Preserve provider-native task
   identity locally. Require every explicit source to refer to the same task;
   a mismatch blocks rather than silently merging projects or runs.
2. Build an inventory of expected executor threads, provider runs/attempts and
   resumed sessions from the handoff and accessible task records. Distinguish
   stable harness `RUN_ID` from provider run/turn ids. Separate top-level
   threads require explicit task linkage; a title match is not enough.
3. Read accessible task-scoped lifecycle/activity metadata, provider usage
   records, phase checkpoints, review verdicts, validation results, browser/QA
   reports and E2E outcomes. Use available native read tools or approved local
   artifacts; do not scrape unrelated histories, persistent memories or
   credential stores. Reading current model configuration alone does not
   prove the configuration of historical attempts.
4. Reconcile each source once. Retain expected/covered/missing/duplicate counts
   and missing identifiers. If the expected inventory cannot be established,
   mark coverage unknown; do not declare the whole task measured from the main
   thread alone. Missing end times and unsettled usage stay pending/unavailable.
5. Give every round an id, kind, outcome, source reference and candidate SHA.
   Preserve failed or superseded candidates, retries, scope changes and aborted
   attempts. A gate without candidate binding is a coverage limitation, not proof
   that the final result passed it. Task success comes from the caller's
   acceptance evidence; delivery readiness is not merge or production rollout.
6. Classify correction causes only when the record supports them: implementation
   defect, missed requirement, changed scope, missing context, environment,
   unstable test, or unknown. Source a classifier judgement and distinguish it
   from an observed verdict. Repeated loop checkpoints alone are not rework.

Maintain a local ledger mapping opaque `source_id` values to actual artifact or
tool observations and original counters. Raw sources remain outside the remote
payload and outside commits. Read only the scope necessary for this report;
never copy sensitive source passages into shared evidence or uploads.

## Checkpoints and later integration

This skill consumes recorded observations; it cannot recover events that were
never stored. A delivery integration should supply tool-timestamped task/phase
boundaries, executor linkage, blocked/resumed states and results. Reuse native
history when equivalent; any supplemental records belong to individual
executors under task-owned ignored runtime paths to avoid concurrent overwrite.

The installed delivery/continuation hooks supply local checkpoints through
`references/checkpoint-capture.md`. Consume their ledger from the caller's
private runtime pointer; a phase checkpoint is not continuous actor activity.
Native token adapters remain provider/runtime-dependent. If an installation
lacks capture or accessible sources, expose the gap rather than promising exact
timing. Historical pilot reports and `<paths.runs>/.metrics/` remain valid inputs.
