# Adopt category and high-risk rules without discarding project rules

Run this check independently of repository-root upgrade-note availability. It is
a wording upgrade for the project's `SDLC.md`, not authority to relabel existing
PRs, change accounts or weaken required QA.

1. Confirm the complete pinned package was updated by its owning installer, as
   in `references/verification-reuse.md` step 1. Do not hand-edit installed
   managed copies.
2. Inspect the project's `SDLC.md` label section and compare it with the
   installed `apptrick-set-up` SDLC template. Propose focused edits only where the
   project still carries the generated wording:
   - **Category.** After the label-group table, add the paragraph and
     change-to-category table that start "Category labels feed the changelog".
     Review now corrects a missing or wrong category itself; a label fix is not
     a finding.
   - **High-risk diff.** Replace the generated `risk-high` bullet ("auth,
     sessions, data scoping, money, schema migrations, shared contract
     surfaces, or broad cross-cutting edits", or in a discovery-layer SDLC
     "authentication and login sessions, data scoping, money, ...") with the template's bullet and its
     high-risk diff table plus the "Tightening is not widening" paragraph. A
     discovery-layer SDLC also points its "No self-QA on `risk-high`" rule at
     that table.
3. Keep project-specific risk areas, stricter local rules and any customized
   label section; report them instead of overwriting. `prTitleTemplate`,
   `ticketKeyPattern` and `dependencyAudit` are optional keys with defaults: do
   not add them to an existing config unless the owner asks.
4. `--dry-run` writes nothing; `--yes` alone permits only non-conflicting
   generated-wording edits. Run the affected project verifier, confirm a second
   inspection proposes no further edits, then report changed files and retained
   local rules.

The canonical source owner delivers this procedure and source revision. Each
installation owner adopts it separately; source acceptance does not claim
deployment to installed adaptations.
