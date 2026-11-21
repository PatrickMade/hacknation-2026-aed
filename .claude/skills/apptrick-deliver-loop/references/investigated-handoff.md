# Investigated handoff boundary

Before any mutation, require an inherited `RUN_ID`, canonical task binding when
the provider requires one, a resolved `--spec`, and that spec/handoff's `Route:`
plus `Evidence:` lines from `apptrick-deliver`.

Missing route evidence means investigation has not run. Invoke
`apptrick-deliver` once with the original accepted arguments plus `--loop`,
relay its result, and stop this fresh path. The primary later hands the same run
back here with route evidence, so that accepted handoff proceeds without
reinvoking the public entry.

The primary invokes this engine from its already-owned isolated worktree after
spec resolution. Verify the inherited repository, task branch, `RUN_ID`, spec
path and clean base identity, then reuse the current worktree without reset,
checkout, or dependency reinstall. Preserve uncommitted spec/evidence bytes until
the run folder's first commit. A mismatch blocks; never create a second worktree
or discard the first one's state.

Search for existing work before creating the run folder. An open matching PR
hands off to `apptrick-continue-pr-loop` with the same `RUN_ID`. A legacy branch,
plan or run folder without a PR has no supported continuation interface: stop for
manual recovery, preserve all state, and do not create a new run or PR.
