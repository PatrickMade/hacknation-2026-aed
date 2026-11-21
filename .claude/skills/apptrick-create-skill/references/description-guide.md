# Crafting the frontmatter `description` (the routing surface)

How `apptrick-create-skill` writes a skill's `description`. It is an important
routing surface: the host may expose it for skills discovered and
eligible in the current session. Discovery roots, configuration and invocation
policy can filter the catalog; an installed file alone does not prove exposure
or selection. Used in author mode; in split mode the existing `description` is preserved
unchanged.

## What a good skill description contains

- **A one-line "what it does + what it produces"** - the outcome, not the mechanism.
- **An explicit "when to use"** with concrete **trigger phrases**, in **English**
  - every description in the collection routes on English triggers. Quote the
  phrases the way a user actually types them: `"create a skill for…"`,
  `"new apptrick-skill"`, `"split this skill"`, `"refactor SKILL.md"`.
- **Disambiguation from siblings** when a nearby skill overlaps - say what this
  one is *not* for (e.g. "use the plain X for small fixes").

## Rules

- **"When to use", not "how it works".** Implementation detail belongs in the
  body, not the routing line.
- **Keep it tight.** Descriptions included in the host's catalog consume context.
  Keep the capability, outcome and useful triggers; check the actual catalog
  before claiming coverage or context savings.
- **No forbidden literals.** The `description` is scanned by `scripts/lint.sh`
  like the rest of the skill - keep it product-agnostic (see
  `references/repo-invariants.md`).
- **Stable across a split.** When refactoring an existing skill, do not touch the
  `description`'s meaning; routing depends on it and the gate verifies it is
  unchanged.

## Shape to aim for

> `<one line: what it does and produces>. <optional disambiguation from a sibling>. Use when the user says "<trigger>", "<trigger>", "<trigger>", "<trigger>".`

Draft it, then read it back cold: from this line alone, would the model know to
pick this skill over every other for the intended request - and know *not* to pick
it for adjacent ones?
