# Worktree setup - isolated worktree and spec branch

Detailed procedure for step 2 (create) and step 8 (cleanup) of `apptrick-publish-spec`. Never run in the user's primary worktree.

## Create the worktree and task branch (step 2)

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
GIT_DIR=$(git rev-parse --git-dir)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir)
WORKTREE_PARENT="$REPO_ROOT/.ai/tmp/apptrick-publish-spec"
CREATED_WORKTREE=0
# Resolve BRANCH from repository instructions/config before this block. For
# Jira/Linear issue work it includes the native key and task-title slug.
: "${BRANCH:?Resolve the project-required task branch before creating a worktree}"

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
- Always clean up the temporary worktree at the end, but only if you created it this run.

## Cleanup sequence (steps 2 and 8)

Run in a `trap`/finally so crashes also clean up:

```bash
cd "$REPO_ROOT"
if [ "$CREATED_WORKTREE" = "1" ]; then
  git worktree remove --force "$WORKTREE_DIR"
fi
git worktree prune
```

## apptrick-publish-spec specifics

- Resolve the branch from repository instructions/config. Jira/Linear issue-driven branches include the validated native key plus task-title slug; GitHub-only and brief-only work retains the repository's established convention. Always detach from `origin/$BASE_BRANCH`.
- A spec run is docs-only: the dependency-install step is usually unnecessary. Install only when step 5's mockup/screenshot capture needs the app booted, and even then prefer the shared test environment the `apptrick-prepare-test-env` descriptor provides over provisioning inside this worktree.
