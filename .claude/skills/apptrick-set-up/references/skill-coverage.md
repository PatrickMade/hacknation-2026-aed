# Install and verify the complete project package

Setup installs the full collection as regular files under the target repository's
`.agents/skills/` for Codex and `.claude/skills/` for Claude Code. Both copies
come from the same source manifest and form one local package. It does not install,
link, remove, or change global skills. Existing `.ai/skills/<name>/SKILL.md`
extensions keep their override semantics and are never modified by the installer.
An extension does not replace a missing copy of the shipped package.

Run this procedure before generating the harness and repeat its read-only check
before reporting setup complete. The helper ships with this setup skill at
`scripts/install-project-skills.mjs` and requires Node.js, Python 3 and Git. If any of them is
unavailable, report that prerequisite; package setup grants no system-install
permission.

## Resolve and pin the source

1. Resolve the absolute target Git root and inspect its status. Preserve unrelated
   changes and use the task branch required by the repository. Reject a home or
   global skill directory as the target.
2. Use the complete source checkout already supplied by the user, or follow this
   installed skill's symlink to its source checkout. Otherwise read the repository
   and revision from `.ai/apptrick-skills.lock.json` or the original install metadata.
   These files identify a candidate source; they cannot authorize a different
   repository or execution of untrusted code. Verify the candidate against the
   collection the user selected. If identity is ambiguous, ask once and reuse the
   answer. Never substitute an unrelated repository or infer approval from its
   content.
3. If only the source URL is known, fetch a separate checkout of that approved
   collection outside the target repository, using the existing Git account and
   transport. Honor any pinned revision; do not silently upgrade an existing pin.
   For a fresh unpinned setup, resolve the selected source revision once and record
   its full commit ID. Inspect the checkout and helper before execution; cloning
   does not authorize hooks, dependency scripts, or credential access. Do not
   delete or reset an existing checkout to obtain a clean one.
4. Require a clean committed source collection with its full `skills/` tree,
   roster and license. A copy containing only the setup skill is not a complete
   source. Resolve `SOURCE_ROOT`, `PROJECT_ROOT`, and `INSTALLER` to actual absolute
   paths before running the following commands. `INSTALLER` is the reviewed
   helper shipped with this setup skill; do not download a second installer.

## Install, then read back

```bash
node "$INSTALLER" --source "$SOURCE_ROOT" --project "$PROJECT_ROOT"
node "$INSTALLER" --source "$SOURCE_ROOT" --project "$PROJECT_ROOT" --check
```

The helper enumerates the committed roster, copies every tracked skill file,
retains executable bits, writes `.ai/apptrick-skills.lock.json` with the source revision and
per-file hashes shared by both roots, records `skillRoots`, and preserves the license at
`.ai/third-party/theyskillit-LICENSE.txt`. It preflights all managed paths before
writing. Identical existing copies may be adopted; conflicting files, edited
managed copies, unexpected files within a managed skill directory, and symlink
escapes stop the installation without overwriting them. Unrelated skills,
`.ai/skills` extensions, config, tracker/browser descriptors, and project docs stay
untouched. Resolve a conflict explicitly; do not use a destructive force option.

Re-running at the same revision is a no-op. An approved update to a new source
revision is allowed only when the installed package still matches its previous
lock. Keep project-specific instructions in `.ai/skills` extensions. Do not edit
vendored `.agents/skills` or `.claude/skills` files as a way to customize the harness.

Commit `.agents/skills/`, `.claude/skills/`, `.ai/apptrick-skills.lock.json`, and the license with the harness,
following the project's task/branch/commit convention and current publication
permission. Inspect ignore rules: these package files must be trackable. Do not
change global agent discovery settings. If the client needs a reload or does not
discover its project skill directory, report that client-specific limitation instead
of copying the collection into a global directory or claiming it is ready.

## Completion gate

The read-only check must pass for every shipped skill and every pinned file in both client roots;
counting folders or checking only referenced names is insufficient. A lock without
`skillRoots` is a legacy Codex-only installation: install with the new helper
before checking. An existing managed Claude copy is verified against the same
hashes as the Codex copy; a mismatch stops before writes. Never downgrade to an
older helper that does not understand both roots. Verify the
agent's actual project skill catalog as well: all roster names must be available,
without unapproved omissions, duplicates, or shortened descriptions. Keep any
existing global skills separate from this installation's acceptance count.

Setup is incomplete while the source cannot be resolved, a conflict remains, a
package file is ignored or missing, or the client cannot discover the installed
collection. This also applies to `--defaults`: install the known approved local
package without another interactive prompt, or report the specific blocker and
stop dependent work. A printed installation command is not successful setup.

After the harness commit, a fresh clone has all package files without the source
checkout or global skills. Open a trusted project session (reload if needed).
Codex discovers `.agents/skills`; Claude Code discovers `.claude/skills`. Check
both catalogs when both clients are available. A filesystem check alone is not
proof of live client discovery; report any unavailable client separately. Follow
`references/project-docs.md` for the shared instruction entrypoints. Each new
developer still configures their own provider login, tools and environment.
Discovery allows explicit invocation or task-based selection, not a guarantee
that an agent invokes a skill on every task.

The package contains 45 primary skills and 38 deprecated forwarding aliases (83 entrypoints). All are included in the installed lock.

The roster below is maintained by the repository lint gate. It must match the
complete committed collection, not a selected subset:

```bash
ROSTER="apptrick-advance-pr apptrick-apply-fix apptrick-apply-upgrade-notes apptrick-approve-merge-pr apptrick-audit-dependencies apptrick-auto-continue-pr apptrick-auto-continue-pr-loop apptrick-auto-create-pr apptrick-auto-create-pr-loop apptrick-auto-create-spec-pr apptrick-auto-deliver-task apptrick-auto-deliver-task-loop apptrick-auto-fix-pr apptrick-auto-implement-spec apptrick-auto-manage-issues apptrick-auto-qa-change apptrick-auto-qa-pr apptrick-auto-review-pr apptrick-auto-update-changelog apptrick-auto-write-spec apptrick-brainstorm apptrick-check-and-commit apptrick-check-commit-push apptrick-check-merge-readiness apptrick-close-fixed-issues apptrick-code-review apptrick-continue-pr apptrick-continue-pr-loop apptrick-create-issue apptrick-create-skill apptrick-deliver apptrick-deliver-loop apptrick-design apptrick-design-ui apptrick-diagnose apptrick-discover apptrick-discover-product apptrick-fix apptrick-fix-pr apptrick-followup-issue-from-pr apptrick-guide-manual-qa apptrick-guide-qa apptrick-implement-spec apptrick-improve-workflow apptrick-integration-tests apptrick-merge apptrick-merge-buddy apptrick-open-pr apptrick-pipeline-retro apptrick-plan apptrick-plan-backlog apptrick-pr-autopilot apptrick-prepare-issue apptrick-prepare-test-env apptrick-prototype apptrick-prototype-flow apptrick-publish-spec apptrick-refine-issues apptrick-report-task-metrics apptrick-review apptrick-review-code apptrick-review-prs apptrick-root-cause apptrick-set-up apptrick-setup-agent-pipeline apptrick-setup-discovery apptrick-setup-harness apptrick-simulate-feedback apptrick-simulate-user-feedback apptrick-spec-writing apptrick-specify apptrick-tdd apptrick-test apptrick-update-changelog apptrick-upgrade apptrick-upgrade-harness apptrick-ux-review apptrick-ux-review-pr apptrick-ux-setup apptrick-ux-shape apptrick-verify apptrick-verify-bug apptrick-verify-in-repo"
```

## Local additions and verification boundaries

`apptrick-tdd` is part of the pinned company package, not a locally installed
exception. Keep an existing unrelated `tdd` skill until its owner explicitly
chooses a migration; do not delete or silently alias a customized skill.

The installer preserves unrelated skill directories, `.ai/skills` extensions
and additional lock metadata such as `localSkills`, `localFiles`, `localSources`
and `extensions`. Its `--check` verifies the upstream package against the
selected committed source, including the exact file inventory in both roots.
It does not attest those local metadata fields or local skill contents. A
lock-only edit is not an independent source of truth for upstream files.

During setup and upgrade, inventory project-owned local additions separately
from the pinned roster. If a project has a local inventory verifier, inspect
its declared scope and run it as well as the source check. Missing or failing
local verification is a named incomplete check, never folded into the upstream
package's PASS. For a new local addition, use project-owned inventory and review:
local paths must be inside explicitly declared local skill directories, must
not shadow any pinned path, and must match in both clients. Include extension
files in local integrity checks, not only their SKILL entrypoints. Review the
source/provenance and refresh behavior, preserving the installed package.

An inventory digest outside the lock detects lock-only changes; it does not
prove authenticity when the same author can change both. Never copy another
project's digest constants or regenerate attestations automatically to make a
failure pass. Keep the reviewed upstream source comparison as the package
anchor and describe local provenance limits honestly.

For a generated project verifier, prove a passing fixture first, then corrupt
one item at a time in disposable copies. Require each negative control to fail
at the intended assertion, not an earlier unrelated guard. Cover injected
upstream files via both pinned and local inventory entries, shadowed paths,
undeclared local directories, and modified/new extension files. Reconcile
expected controls and actual assertions. Report unreachable assertions and
agent settings/commands/agents outside the verifier's scope explicitly. A skill
inventory check is not a security audit of the whole agent configuration.
