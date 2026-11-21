# Worktree setup - isolated worktree and task branch

Detailed procedure for step 6 (create) and step 13 (cleanup) of `apptrick-deliver`. Never run in the user's primary worktree.

## Create the worktree and task branch (step 6)

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
GIT_DIR=$(git rev-parse --git-dir)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir)
WORKTREE_PARENT="$REPO_ROOT/.ai/tmp/apptrick-deliver"
CREATED_WORKTREE=0

if [ "$GIT_DIR" != "$GIT_COMMON_DIR" ]; then
  WORKTREE_DIR="$PWD"
else
  WORKTREE_DIR="$WORKTREE_PARENT/${SLUG}-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$WORKTREE_PARENT"
  git fetch origin "$BASE_BRANCH"
  git worktree add --detach "$WORKTREE_DIR" "origin/$BASE_BRANCH"
  CREATED_WORKTREE=1
fi

cd "$WORKTREE_DIR"
git checkout -B "$BRANCH" "origin/$BASE_BRANCH"
```

Then install dependencies with whatever the repository's lockfile implies (npm, pnpm, bun, cargo, etc.); skip when the project needs no install step.

Rules:

- Reuse the current linked worktree when already inside one. Never nest worktrees.
- The main worktree must stay untouched.
- Remove a temporary worktree only when its task state is committed and pushed and
  `git status --porcelain` is empty. Preserve an incomplete/dirty worktree and
  report its path and recovery command; cleanup must never discard evidence.

## Cleanup sequence (steps 5 and 13)

Run in a `trap`/finally, but remove only a clean, fully persisted worktree:

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
