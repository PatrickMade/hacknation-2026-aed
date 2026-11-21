# Worktree setup - isolated worktree and task branch

Detailed procedure for step 6 (create) and step 14 (cleanup) of `apptrick-deliver-loop`. Never run in the user's primary worktree.

## Reuse the verified handoff worktree (step 6)

The public entrypoint already created the task worktree and installed needed
dependencies. Require the verified inherited repository, task branch, base
identity and `RUN_ID` from `references/investigated-handoff.md`. Check the actual
worktree path and current branch against that handoff. Stop on mismatch.

Do not run `git checkout -B`, reset, create another branch/worktree, or reinstall
dependencies. Preserve uncommitted spec and diagnostic evidence until the first
run-folder commit. Retain inherited `REPO_ROOT`, `WORKTREE_DIR` and
`CREATED_WORKTREE` for terminal cleanup; the loop becomes their sole cleanup owner.

Never discard dirty or unpushed work. Preserve an incomplete worktree and report
its path and recovery command.

## Cleanup sequence (steps 6 and 14)

Run in a `trap`/finally, but remove only a clean, fully persisted worktree
(registered at creation time, executed at run end):

```bash
cd "$REPO_ROOT"
if [ "$CREATED_WORKTREE" = "1" ]; then
  if [ -z "$(git -C "$WORKTREE_DIR" status --porcelain)" ] &&
     git -C "$WORKTREE_DIR" rev-parse --verify '@{upstream}' >/dev/null 2>&1 &&
     [ -z "$(git -C "$WORKTREE_DIR" rev-list '@{upstream}..HEAD')" ]; then
    git worktree remove "$WORKTREE_DIR"
  else
    printf 'Preserved incomplete worktree: %s\n' "$WORKTREE_DIR" >&2
  fi
fi
git worktree prune
```
