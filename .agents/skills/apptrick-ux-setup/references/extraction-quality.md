# Source provenance and rule confidence

## Before extraction

Read build configuration, ignore rules and component/theme entrypoints to select
the source roots. Exclude compiled bundles, generated clients, dependency trees,
coverage, screenshots and scratch output even when Git already ignores them;
the extractor may still scan ignored files. Do not assume a fixed output-folder
name. Use the pinned extractor's documented input/exclusion options when present.
If it cannot restrict inputs, use a task-owned filtered source copy preserving
relative paths and the existing manual section, or the manual fallback from
`references/contract-format.md`. Do not delete or move the developer's build
output to make extraction pass. Never run executable code from a filtered copy.

## Before accepting the result

- Verify token source paths, component files and canonical screen examples exist
  inside the actual repository's reviewed source roots. A generated-output source
  is contamination regardless of its percentage; exclude it and re-extract.
- Check token declarations and their actual consumers. For example, channel-only
  CSS values wrapped by a theme function may be color tokens even if the
  extractor labels them `other`. Report the limitation; do not invent a new
  palette or claim the extractor's counts are authoritative design decisions.
- Check native-element mappings against imports and the repository's established
  wrappers. A registered component is not automatically the preferred component.
  Multiple active component libraries or themes are an open decision unless
  project instructions or a confirmed team rule resolve it.
- Distinguish observed usage, confirmed rules and advisory proposals. Record the
  source of confirmed rules in the manual section. Put unresolved generated
  mandates there as explicit advisory overrides, so a later sync cannot silently
  turn them into enforced rules. Do not treat raw colors, library selection or
  an unconfirmed theme as a product violation merely because the extractor does.
  This does not suppress independently evidenced usability/accessibility defects.
- Read back the manual section after refresh and compare it with the pre-refresh
  content. Preserve prior decisions and add only authorized updates. Inspect the
  generated diff and its cited sources before reporting completion.

## Acceptance examples

A repository with two active UI libraries and compiled CSS in an ignored build
folder yields source-backed inventory and an advisory library choice. It must
not mandate one library or count compiled CSS as an independent design source.
A repository with a documented default component and palette retains those
confirmed rules after regeneration. A missing source file or lost manual section
leaves the affected contract incomplete; counts alone cannot make it pass.
