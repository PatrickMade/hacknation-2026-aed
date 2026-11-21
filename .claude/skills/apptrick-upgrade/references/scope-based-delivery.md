# Adopt scope-based delivery without discarding project extensions

Run this check independently of repository-root upgrade-note availability. This
is a source-policy upgrade for project instructions and configuration, not
authority to install packages, weaken required QA, change accounts, upload
metrics or deploy anything.

1. Confirm the complete pinned package was updated by its owning installer, as
   in `references/verification-reuse.md` step 1. Do not hand-edit installed
   managed copies; a modified managed file is a conflict for its local owner.
2. Inspect the effective AGENTS/CLAUDE instruction owner, `SDLC.md`,
   `CODE_REVIEW.md`, repo-local skill extensions and `.ai/agentic.config.json`.
   Follow imports to the real owner; never append to a pointer-only bridge.
3. Compare the project documents with the installed `apptrick-set-up` templates and
   propose focused edits only where the project still carries the generated
   wording:
   - **Tests.** The SDLC Implement row says "implement the change with tests that
     prove it, reusing existing coverage". Replace generated wording that
     requires new regression tests for every change. Keep project rules that
     require specific tests, and keep bug regression and RED/GREEN rules.
   - **Small-change spec record.** The SDLC Task specifications section accepts
     an existing task record placed in the specs directory as the covering spec
     for one small agreed change. Keep the project's spec-file requirement and
     any stricter local rule.
   - **Scope and completion.** The generated `## Scope and simplicity` block in
     AGENTS carries "Once acceptance criteria and required gates pass, stop.
     Report material out-of-scope findings without implementing them." Add it
     only when the block exists and has no equivalent rule.
4. **Metrics key.** Detailed time/token capture is opt-in. Preserve an explicit
   `metrics.enabled` value, including an existing `true` written by an earlier
   upgrade, and every transport binding. Leave a missing key unset; the
   installed helpers then keep capture off. Report the opt-in change and that a
   project enables measurement with `"metrics": { "enabled": true }`. Never
   flip an explicit value. A config with a bound `metrics.transport` but no
   `enabled` key stops capturing under the new default: report it as an explicit
   owner decision (enable or leave off) and do not change it.
5. `--dry-run` writes nothing; `--yes` alone permits only non-conflicting
   additive or generated-wording edits. Customized or conflicting rules keep the
   normal upgrade approval boundary and are reported, not overwritten. Retain
   task/spec/run/PR identity, evidence and history.
6. Run the source-backed package `--check` and the affected project verifier.
   Confirm a second inspection proposes no further edits, then report changed
   files, retained local rules, the metrics setting and unresolved conflicts.

The canonical source owner delivers this procedure and source revision. Each
installation owner adopts it separately; source acceptance does not claim
deployment to installed adaptations.
