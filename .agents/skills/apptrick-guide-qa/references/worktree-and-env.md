# Test checkout and environment

For a PR, resolve the target repository and full head SHA through the tracker.
Reuse an existing test checkout only when its recorded task/run ownership and
revision match. A linked worktree alone does not establish ownership. Never
repoint another task's checkout or overwrite changes. Otherwise create a new
isolated detached worktree at the verified SHA and record its absolute path,
run identity and creation ownership. A fetch or checkout failure is a blocker;
never switch the user's primary checkout as a fallback.

Local mode observes the current checkout without stash, reset or branch changes.
Record its dirty state so evidence is not presented as a clean committed build.

Use `apptrick-prepare-test-env` for readiness, source revisions, UI/API URLs, required
services, TTL and process ownership. Read its descriptor and the browser provider
on every operation. Login uses approved credential references through the
supported secret mechanism; never source an arbitrary credential file as shell
code, print credentials or embed them in the runbook.

Manual UI actions must remain within the approved scenario and environment.
Report unavailable prerequisites as blocked cases. On exit close only this run's
owned browser/environment and remove a test worktree only when the recorded
ownership matches and there are no unpreserved changes. Keep evidence artifacts.
