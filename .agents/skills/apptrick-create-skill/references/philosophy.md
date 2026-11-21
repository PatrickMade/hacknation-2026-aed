# The layering philosophy, as an operational checklist

How `apptrick-create-skill` decides what stays in the body and what goes to
`references/`. This shipped reference owns the layering decision for both modes;
no separate repository-root philosophy document is required.

## The three loading layers dictate the split

| Layer | What | When it loads | So… |
| --- | --- | --- | --- |
| 1. `description` (frontmatter) | capability and "when to use" | when the host includes the skill in the current catalog | keep routing concise; verify exposure on the claimed host |
| 2. `SKILL.md` body | the instructions | when the host or agent loads the selected entrypoint | keep what's needed to orchestrate and choose a branch |
| 3. `references/…` | detail, templates, branches | when the agent or host actually reads the required file | place branch detail here and give an explicit read condition |

These are instruction layers, not delivery guarantees. A pointer does not itself
load a file, and installation does not prove catalog visibility. Require the
entrypoint and applicable references to be read before dependent actions. If a
required file cannot be read, stop those actions and name the missing dependency.
Use `references/gates.md` to distinguish source checks from delivery and behavior.

Overriding rule: **`SKILL.md` = router + map. `references/` = the terrain.**

## The up/down decision - ask in this order, per fragment

1. **Is it needed to *pick* this skill?** → it belongs in `description` (layer 1). One sentence.
2. **Is it needed on *every* run to orchestrate the flow or choose a branch?** → keep it in the body (layer 2), but condensed: a one-liner + a pointer.
3. **Is it a one-branch detail / template / table / checklist, used only *after* entering a specific step?** → move it to `references/` (layer 3).

## Heuristics

- **Output template → always layer 3.** Long "this is what the PR comment / QA report looks like" blocks are needed only in the step that produces them.
- **Conditional section → layer 3.** If it runs only in one branch (`if fork`, `if --stop`, `if first run`), it should not load on every run.
- **Reference table > ~15 rows → layer 3**, unless the model needs it for the branch decision itself.
- **Safety loads on every run.** The untrusted-content boundary, no-exfiltration rules, and QA gates must be visible whenever the skill runs - in the body, or in the step-0 `references/agentic-setup.md` the body always loads first. Never hide safety behind a conditional lazy-load.
- **Decision logic stays in the body.** The *premise* that selects a branch stays up; only the *content* of the branch goes down.

## The readability test (the gate for "did I split well?")

Read the body alone after the split. If you can still tell **what** the skill
does, **in what order**, and **where** to look for detail - the split is good. If
the body became an unreadable list of links with no flow logic - you overdid it;
pull some back up.

## Don't over-split

- Skills under ~150 lines usually stay whole - the whole thing is one coherent thought; splitting only adds a load hop.
- Don't extract a fragment that loads on every run anyway - you gain only a round-trip.
- Don't split so finely that the map is longer than the terrain. A step describable in 3 lines stays 3 lines in the body.

## Conventions for the reference files

- Live under `references/` in the skill's own directory (the one established pattern).
- kebab-case names describing the *content*, not a step number: `pr-summary-template.md`, `fork-pr-flow.md` - not `part1.md`.
- Each reference file opens with one sentence: what it is and which skill/step calls it.
- Link from the body with a sentence that says *when* and *why* to load the file, not a bare link.
