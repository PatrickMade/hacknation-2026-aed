# Classify waiting from evidence

Use this procedure when analysing delivery intervals or recording wait
checkpoints. Preserve the calendar span and sources; classification selects the
appropriate metric without deleting the original observation.

1. Identify what prevented progress and which actors were affected. A pending
   required human decision, approval, credential entry or acceptance is a
   `human_block` only for the evidenced waiting interval. An explicit stop or
   suspension is `suspended`. Builds, tests, CI, required infrastructure queues
   and test-environment locks are `technical_wait`. User absence alone is not
   a block while linked agents can continue the task.
2. Require evidence of entry and exit, or retain the open/missing boundary as
   a coverage gap. Match the executor/run inventory and clock. Capture observed
   transitions in the existing ledger; keep the detailed reason/source locally.
   Do not introduce new event fields or publish private explanations. A current
   checkpoint cannot retrospectively timestamp an unobserved past transition.
3. Distinguish one actor from the whole task. A coordinator awaiting working
   children has not suspended the task. Subtract a task-level human block or
   suspension only when sources establish that no linked task work could proceed
   during that interval. Uncertain overlap remains unknown; do not subtract a
   parent's inclusive wait from a child's real activity.
4. Derive `calendar_ms` from evidenced task boundaries. Derive `delivery_ms`
   under the contract by subtracting the union of proven whole-task human blocks
   and suspension, without duplicate overlaps. Required technical waits remain
   included. Direct actor activity requires its own sources; neither calendar
   nor adjusted delivery is computationally active time.
5. A silent gap, open provider session, running status or absence of human-block
   events does not prove activity or zero human waiting. There is no automatic
   long-gap cutoff. If state/clock/lifecycle evidence cannot classify a material
   interval needed by the selected metric, keep full adjusted delivery null and
   coverage partial/unavailable; retain known calendar or interval quantities
   separately as allowed by the report contract. Set a wait quantity to zero
   only when the relevant coverage proves its absence, otherwise keep it
   unavailable. An old completeness flag, schema validation or receipt
   establishes no missing state evidence.
6. Hand back measured/reconstructed/unavailable quantities, coverage limits and
   publication status separately. Never edit stored revisions to improve their
   apparent accuracy. A later sourced correction follows the existing revision
   and receipt procedure; uncertainty alone does not authorise a submit.

Examples:

- An agent explicitly requests approval at18:00; all task work is blocked until
  approval at09:00. With evidenced boundaries,15h stays in calendar time and is
  excluded from adjusted delivery. It is not15h of human labour.
- The senior is away, but an implementation child runs tests for2h. That work
  remains part of delivery; senior absence does not remove it.
- CI occupies40min. It contributes to delivery and the sourced technical-wait
  quantity, without adding40min again to elapsed time.
- A timeline jumps from18:00 to09:00 with no state evidence. Preserve the gap;
  do not label it active, human-blocked or suspended from its length.
