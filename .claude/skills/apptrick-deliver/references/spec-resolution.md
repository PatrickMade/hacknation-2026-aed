# Covering spec resolution

Resolve `SPECS_DIR` from `paths.specs` in the loaded project config (default
`.ai/specs`) before the first lookup, including intake before worktree creation.
Resolve an explicit or inferred spec reference read-only. Try in order; first
unambiguous hit wins:

1. **Path** - an existing repository-relative file under `$SPECS_DIR` or another
   allowed project path.
2. **Name or slug** - case-insensitive filename match in `$SPECS_DIR`, with or
   without the date prefix and `.md`, then exact `# {Title}` match. Pick the newest
   dated candidate only when its title is unambiguous; otherwise list candidates.
3. **Issue reference** - use **get-issue** and complete comments to find links or
   paths to `$SPECS_DIR` files or a design-only spec PR. Preserve the canonical
   issue id for linkage.
4. **Spec PR** - use **get-pr** when the reference is a PR or the issue points to
   one. Accept a file added under `$SPECS_DIR`; also use **search-prs** to detect an
   open PR for a resolved spec path. Record `SPEC_PR`, but keep that PR/branch
   design-only: copy the spec into the new task branch and publish implementation
   on exactly one separate implementation PR.

After lookup, assess coverage using the Task specification gate in
`references/agentic-setup.md`. Accept a short manual or user-supplied spec when
it contains that gate's required content, including verification/implementation
steps. `Implementation Plan` and `Phasing` (with or without glossary emojis)
are useful headings, not mandatory names. Preserve equivalent sections and
derive the separate execution plan from their content without rewriting the
spec just to match a template.

A missing explicit reference or multiple ambiguous matches stops with:

```text
Status: blocked
Spec not found for "{spec}".
Searched: path, $SPECS_DIR name/title match, issue links/comments, spec-PR branches.
Closest candidates:
- {path} - {title}
Next: pass an exact path, or create the missing covering spec first.
```

An existing but incomplete spec is not a failed lookup: report its path and the
missing content. After investigation and ownership checks, extend it through the
Task specification gate before implementation, preserving the supplied scope and
provenance. Unresolved material decisions remain blocking.

An inferred missing spec follows the same gate: after route analysis, invoke
`apptrick-specify` in the already-owned worktree. Never invoke another
implementation or delivery entrypoint to resolve or implement a spec.
