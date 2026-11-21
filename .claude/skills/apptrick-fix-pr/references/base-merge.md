# Merge the latest target branch into the PR - first

The step-3 procedure `apptrick-fix-pr` runs before any review or CI work, so the
whole loop judges the real merge result against the PR's current target.

The base here is the PR's own target. Resolve `TARGET_BRANCH` from this PR's
**get-pr** `baseRefName` before this procedure and on each later cycle,
validate it as a branch name and keep it quoted. A stacked PR targets another
PR's branch, so substituting the configured `baseBranch` or the repository
default would pull unrelated commits into it; an unavailable target is a
blocker instead. Diffs and required-check lookups use the same target. A
replacement PR keeps that target. If the PR is retargeted, earlier review and
CI readings no longer describe the merge result: evaluate them again.

## Same-repo PR head

1. `git fetch origin "$TARGET_BRANCH"` to get the latest target tip.
2. Merge it into the checked-out PR branch: `git merge --no-edit "origin/$TARGET_BRANCH"`.
3. **Conflicts**: resolve trivial ones directly (import ordering, changelog/lock
   noise, non-overlapping edits). For anything non-trivial - overlapping logic,
   deleted-vs-modified files, semantic conflicts - do **not** hand-resolve blindly:
   let the `apptrick-review` autofix flow (step 4) own conflict resolution, since
   it reuses applicable evidence and runs invalidated checks after each fix. Only pre-resolve here what is
   obviously safe.
4. Run the changed-scope subset of `validation.commands` after the merge to catch
   a merge that compiles but breaks; if it fails and the fix is non-trivial, defer
   to step 4.
5. Push the updated PR branch.

## Fork PR head

A fork head branch usually cannot be pushed to (no write access to the
contributor's fork). Do **not** try to force the base merge onto it here. Instead,
let step 4's `apptrick-review` run its **fork carry-forward flow**: it bases a
new branch in the main repo on the fetched PR head, merges/rebases against the
base there, applies fixes, and opens a **replacement PR** that
`Supersedes #{prNumber}` with credit to the original author (the requirements this
skill verifies on that replacement live in `references/pr-finalize.md`, fork
supersede/credit section). From that point, `{prNumber}` in the rest of `apptrick-fix-pr`
refers to the replacement PR, and the base-merge happens on the carry branch you
can push.

## Re-merging during the loop

The target can advance while the loop runs (other PRs merge). Whenever it does, repeat
this procedure before the next review/CI cycle - a PR that was green against an old
target is not merge-ready. Track the `origin/$TARGET_BRANCH` tip SHA and compare
before each cycle so you only re-merge when it actually moved.
