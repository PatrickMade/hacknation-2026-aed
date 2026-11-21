#!/bin/sh
# Bootstrap step: route Git hooks to the harness hooks, then read the setting back.
# Run from the app checkout after the harness is installed (.ai/hooks/pre-push present and executable).
#
#   sh .ai/scripts/bootstrap-hooks.sh             Default. Shared clone config (git config --local): every worktree
#                                                 of the clone runs .ai/hooks.
#   sh .ai/scripts/bootstrap-hooks.sh --worktree  This worktree only (git config --worktree), for a task worktree
#                                                 whose session must not change the shared clone config. Turns on
#                                                 extensions.worktreeConfig when it is off.
#
# Without either, one push still runs the guard: git -c core.hooksPath=.ai/hooks push -u origin HEAD
# Either way the effective core.hooksPath must read back as .ai/hooks, so no other scope silently overrides it.
set -eu
SCOPE=--local
case "${1:-}" in
  '') ;;
  --worktree) SCOPE=--worktree ;;
  *) echo "usage: bootstrap-hooks.sh [--worktree]" >&2; exit 2 ;;
esac
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
if [ ! -f .ai/hooks/pre-push ] || [ ! -x .ai/hooks/pre-push ]; then
  echo "bootstrap-hooks: .ai/hooks/pre-push is missing or not executable; install the harness first" >&2
  exit 1
fi
if [ "$SCOPE" = --worktree ] && [ "$(git config --bool --get extensions.worktreeConfig || true)" != true ]; then
  # Git requires core.bare and core.worktree to move out of the shared config before worktreeConfig is turned on.
  if [ -n "$(git config --local --get core.worktree || true)" ] || \
     [ "$(git config --local --bool --get core.bare || true)" = true ]; then
    echo "bootstrap-hooks: the shared config sets core.worktree or core.bare=true; move it to config.worktree first (git help worktree, CONFIGURATION FILE) or use git -c core.hooksPath=.ai/hooks push" >&2
    exit 1
  fi
  git config --local extensions.worktreeConfig true
fi
git config "$SCOPE" core.hooksPath .ai/hooks
if [ "$(git config "$SCOPE" --get core.hooksPath)" != ".ai/hooks" ]; then
  echo "bootstrap-hooks: core.hooksPath did not read back as .ai/hooks ($SCOPE)" >&2
  exit 1
fi
if [ "$(git config --get core.hooksPath)" != ".ai/hooks" ]; then
  echo "bootstrap-hooks: another config scope overrides core.hooksPath; git config --show-origin --get-all core.hooksPath names it" >&2
  exit 1
fi
if [ "$SCOPE" = --worktree ]; then
  echo "core.hooksPath=.ai/hooks (worktree)"
else
  echo "core.hooksPath=.ai/hooks"
fi
