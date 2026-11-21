# Exit ramps

The full routing table for `apptrick-brainstorm`'s conclusion (workflow steps 4-5), with decision guidance and boundary cases. The compact table in the skill body is the contract; this file is how to pick the row.

## The table

| # | Conclusion | `Next:` line | Other contract lines | Brief file |
|---|-----------|--------------|----------------------|------------|
| 1 | Question answered, or nothing worth building | `Next: none` | - | no |
| 2 | Worth capturing, not now | `Next: apptrick-create-issue "<one-line goal> - brief: <path>"` | `Brief: <path>` | yes |
| 3 | Feature; blocking unknowns resolved in the conversation | `Next: apptrick-publish-spec "<one-line goal> - brief: <path>"` | `Brief: <path>` | yes |
| 4 | Feature; the user wants to answer the design questions themselves | `Next: apptrick-specify "<one-line goal> - brief: <path>"` | `Brief: <path>` | yes |
| 5 | Small, well-understood change that needs no spec | `Next: apptrick-deliver "<task> - brief: <path>"` | `Brief: <path>` | yes |
| 6 | Already tracked - an existing open issue covers it | `Next: apptrick-deliver <issueId>` | `Issue: {#<n> for GitHub | <native-key> for Jira/Linear} (link: <url>)` | no |

## Picking the row

- **1 vs anything.** If the deliverable of the conversation is understanding - an answer, a decision not to act - stop at ramp 1. Do not manufacture work to have a handoff.
- **2 vs 3/4/5.** Ramp 2 parks; the others start the pipeline now. The question is appetite, and it belongs to the user - ask it plainly ("do it now, or capture it for later?").
- **3 vs 4.** Both end in a feature spec. Ramp 3 when the conversation resolved the unknowns that would otherwise be the spec's Open Questions - the brief's Resolved-unknowns table carries them, and the autonomous spec run uses those answers instead of its own defaults. Ramp 4 when the user explicitly wants to co-design the spec. Did they ask to stay in the loop, or are the unknowns actually resolved? Do not pick 4 out of caution alone - that is what the challenger gate is for.
- **5 vs 3/4.** Ramp 5 when a reviewer would not want a design to react to: the change is small, local, and its shape is obvious from the brief. If naming the affected areas took real work in the conversation, it probably deserves a spec.
- **6 outranks 2.** When step 3 found an existing open issue that covers the idea, route to it instead of filing a duplicate - `apptrick-create-issue` would only rediscover it. When the existing issue is closed, or covers the idea only partially, prefer ramp 2 and say so in the brief; the downstream dedupe step will link the relation.

## Constraints

- **Never route to `apptrick-diagnose` directly.** It requires a verified defect and `{issueId}`; `apptrick-deliver` performs intake and confirmation first. A bug with no issue routes to ramp 2 (the issue carries the analysis) - or ramp 5 when the fix is obvious and small.
- **Args embed the brief path.** The `- brief: <path>` suffix inside the args string is how the routed skill finds the resolved unknowns; the `Brief:` line repeats the path for orchestrators. Keep the path repo-relative and space-free (kebab-case slug) - the `Brief:` line is parsed as `\S+`.
- **Repo-local ramps.** A repo-local extension may append rows routing to repo-specific skills (for example, a repository's own analysis or authoring skills). Added rows follow the same contract shape; the step-5 confirmation gate and the write restrictions stay.

## Brief lifecycle

The brief starts as an uncommitted file in the invoking checkout - `apptrick-brainstorm` never commits (it is read-only plus this one write). Durability is the routed skill's job, and ingestion happens **before any worktree is created** - a worktree branched from `origin` does not contain the file:

- `apptrick-deliver` (ramp 5) reads the brief in the invoking checkout, copies it into its worktree at the same repo-relative path, includes it in the plan commit, and carries the Resolved-unknowns and Non-goals into the plan.
- `apptrick-publish-spec` (ramp 3) feeds the brief to the spec and commits it beside the spec. The Resolved-unknowns table pre-answers Open Questions; autonomous defaults apply only to what it leaves open.
- `apptrick-specify` (ramp 4) uses the same input but leaves the copied brief and spec uncommitted. Its later delivery or publication caller owns committing them.
- `apptrick-create-issue` (ramp 2) embeds the brief's content in the issue body - the tracker copy is the durable one; the local file carries nothing the issue does not.

Published delivery and issue routes retain the Resolved-unknowns table in a committed or tracker-held artifact. The local specification route depends on the local files until its delivery/publication caller commits them; do not claim cross-machine durability before that.
