# Prior specs and spec-code drift (steps 1, 2 and 9)

Use this file when step 1 finds existing specs under `SPECS_DIR` (including
subdirectories) that cover the area the change touches. Without a related prior
spec, skip it: the code is then the only description of current behavior.

It applies only when a spec is written. Whether a change needs one stays with
the project's rule: a task record placed in the specs directory may cover one
small agreed change, and then this file does not apply.

## 1. A new file for new work

When a spec is written for a change on top of earlier work, write it as a new
file (step 2) and leave the prior spec's content as it is. The prior spec stays
the record of what was decided then; the new spec records what changes now, so a
reader can follow both decisions and their dates.

## 2. Classify each related prior spec

For each prior spec covering the affected area, pick one relation and record it
in the new spec's header:

| Relation | When | Header line in the new spec |
|---|---|---|
| Extends | The prior spec stays valid; the new one adds behavior on top of it. | `Extends: <repo-relative path>` |
| Supersedes | The new spec replaces the whole prior spec, or named parts of it, so they stop describing intended behavior. | `Supersedes: <repo-relative path>` (whole) or `Supersedes: <repo-relative path> - sections: <section names>` (partial) |

Write one line per related prior spec and omit the lines when none relates. A
prior spec that only shares the area and is unaffected is not listed. Validate
each path as repository-relative (`^[A-Za-z0-9._/-]+$`, no `..` segment) before
writing it.

## 3. Drift check: prior spec against code

Before the skeleton, compare each related prior spec with the code that
implements it, limited to the modules and contracts the change touches:

- **Not implemented or partial**: the spec describes behavior the code lacks.
- **Diverged**: the code does something else, such as renamed fields, changed
  contracts, or removed or added flows.
- **In sync**: nothing material differs.

The code is the truth about current behavior, because it is what users run
today. The skeleton's "what happens today" and the Architecture section's
current consumers describe the code, not the prior spec.

Record material drift in the new spec under `## 📝 Prior spec drift`, one line
per item: prior spec path and section, what the spec says, what the code does,
and a code reference. Omit the section when everything is in sync.

When it is unclear whether drift is intended or a defect, and the answer changes
the design, raise it as an Open Question. Under `--autonomous`, default to "the
code is the current state; do not design to restore the prior spec's behavior",
and mark `⚠ NEEDS HUMAN CONFIRMATION` when the drift touches security, data
scoping, a `BACKWARD_COMPATIBILITY.md` surface or a `product-brief.md` decision.
Drifted sections the new spec takes over belong in its `Supersedes:` line.

## 4. The one edit to a prior spec

For each `Supersedes:` line, and only for those, insert one annotation line
directly below the prior spec's H1 title in step 9, after the new spec is final:

```markdown
> ⚠️ Superseded by `<repo-relative path of the new spec>` (YYYY-MM-DD) - <whole spec | sections: ...>. Current state: see the new spec.
```

- Keep one line per superseding spec. On a re-run, find the existing
  `Superseded by \`<same path>\`` line and update it in place.
- Leave the rest of the prior spec unchanged; `Extends:` relations and drift
  without supersession leave it untouched.
- Parsers key on the text `Superseded by`, not on the emoji.
- The calling delivery skill commits this line together with the new spec.
