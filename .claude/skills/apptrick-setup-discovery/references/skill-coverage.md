# Product capability coverage

Verify `apptrick-discover`, `apptrick-plan`, `apptrick-prototype` and
`apptrick-simulate-feedback` through the complete project-local package contract
owned by `apptrick-set-up`. Missing coverage is an incomplete setup. Repair
through the existing source-pinned installer; no parallel npx/global installation.
Preserve package locks, local extensions, both client roots and project policies.

For a missing package, resolve a clean source collection checkout and the target
Git root before offering these terminal commands. Replace the placeholders with
verified absolute paths and quote them; do not invent a source revision.

```sh
node "<source-checkout>/scripts/install-skills.mjs" --project "<target-git-root>"
node "<source-checkout>/scripts/install-skills.mjs" --project "<target-git-root>" --check
```

Then invoke `apptrick-set-up` for a new harness or `apptrick-upgrade` for an
existing one. Package installation and configuration migration are separate;
preserve local policy and report missing access or unresolved package conflicts.
