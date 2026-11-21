# Verify generated environment scripts

Generation and repair must verify the public up/down commands, not just a
hand-started app. Use the bundled `scripts/check-test-env.mjs` (Node.js required).
Resolve the actual project root and configured descriptor path before each call.
The checker reads descriptor metadata; it never opens `credentialsFile`.

## Every invocation

Run the check after the up script has written its descriptor and before reporting
success. Bake this call into each generated up-script success path, including warm
reuse, so a direct invocation gets the same check without an agent present:

```bash
node "$CHECKER" --project-root "$PROJECT_ROOT" --descriptor "$ENV_DESCRIPTOR" \
  --ttl-seconds "$TEST_ENV_CACHE_TTL_SECONDS"
```

`CHECKER` must resolve inside the repository. With the full local skill package,
use `.agents/skills/apptrick-prepare-test-env/scripts/check-test-env.mjs`. For a standalone
skill installation, copy the reviewed self-contained helper into `paths.scripts`
and record its source revision when generating the entrypoints. Never commit a
path into another developer's home directory. Pass the same approved
`--allowed-domain` arguments used for the browser wrapper below. Use PowerShell
argument-array equivalents for a native Windows entrypoint.

This check validates descriptor compatibility, paths, freshness, process liveness,
and the recorded browser policy. It cannot prove that a PID belongs to this run,
that teardown is safe, or that a healthy page can reach its API. The generated
scripts must independently verify process identity before reuse or stop: bind the
PID to the process start identity and this checkout/run, and validate the owned
container/volume identities where services exist. PID liveness alone is not
ownership. Verify required application readiness with the project's own probes.

## Browser restrictions on every command

For a domain-restricted agent-browser run, generate an executable wrapper during
setup, using the resolved provider executable and the approved domain list:

```bash
node "$WRAPPER_GENERATOR" --project-root "$PROJECT_ROOT" \
  --output "$BROWSER_WRAPPER" --browser-executable "$BROWSER_EXECUTABLE" \
  --allowed-domain 127.0.0.1 --allowed-domain localhost
```

`WRAPPER_GENERATOR` is this skill's `scripts/generate-browser-wrapper.mjs`.
`BROWSER_WRAPPER` is a repository-relative runtime path under
`paths.qa/browser-policy/`. Ignore that directory in Git: the wrapper and its
policy/config sidecars contain this machine's resolved paths. Keep the portable
generation recipe in the up script and regenerate these artifacts when the local
provider path changes. The generator itself can be copied into `paths.scripts`
for a standalone installation.
The loopback domains above are a local-only example. Derive the real allowlist
from the authorized QA target; do not add staging, production, or third-party
hosts to make a blocked request pass. Review the generated wrapper and policy
sidecar, and use the wrapper's absolute runtime path as `browser.command`.
Keep it a single executable path, never a command string with flags.

Every operation, including open, snapshot, interaction, screenshot, and close,
must invoke that wrapper. The wrapper supplies the restriction each time and
rejects caller overrides. Passing flags only to `open`, or writing a note in the
descriptor, does not enforce a policy. Verify the wrapper on the actual platform, including an allowed local request
and a denied request outside the approved domain list. The installed provider must
support and enforce `--allowed-domains`; reject an unsupported version instead of
silently dropping the flag. If the wrapper cannot be invoked there or either probe
fails, report browser verification blocked. Keep the
legacy Playwright object and provider routing intact. A non-agent-browser provider
needs its own demonstrated policy mechanism; do not apply agent-browser flags to
it or claim equivalent enforcement without a test.

The allowlist constrains browser commands. It does not isolate application-server
traffic, credentials, or every other tool. Preserve the recipe's separate network
and data boundaries and report any API/authenticated-flow limitations.

Apply the authorized target policy separately to the repository test runner,
including Playwright when agent-browser is used for exploration. Validate UI and
API URL overrides before credentials, requests with side effects or screenshots.
Compare parsed HTTP(S) origins/hosts with the approved target scope, never a
substring such as `localhost` in the raw URL; reject userinfo and invalid URLs.
A local-only recipe rejects non-loopback targets. An explicitly authorized
deployed recipe uses its approved target list instead; do not infer authority
from an arbitrary `BASE_URL` override. Redirects and absolute API requests must
remain in scope too. Keep these checks in shared runner configuration/helpers
used by all affected tests, and exercise both an allowed target and a denied
override (including a deceptive hostname) without sending credentials. A passing
agent-browser wrapper test is not evidence that the test runner enforces it.

## Generation and repair gate

After reviewing the generated scripts and their exact target, run the lifecycle
exercise for a disposable environment that this task is authorized to restart:

```bash
node "$CHECKER" --project-root "$PROJECT_ROOT" --descriptor "$ENV_DESCRIPTOR" \
  --exercise --exercise-ttl-seconds 1 \
  --allowed-domain 127.0.0.1 --allowed-domain localhost
```

Use the actual approved domains or omit those arguments when no domain-restricted
browser is part of the recipe. Each entrypoint has a 300-second timeout; use
`--command-timeout-seconds` for a known slower local build, within the task's
execution budget. `--exercise` invokes the public start/stop scripts,
checks cold startup, immediate warm reuse, forced rebuild and restart, TTL expiry and restart, forged
unrelated PIDs during startup and teardown, and repeated teardown. Failed startup
triggers the reviewed teardown even when descriptor validation did not finish. On success it leaves the test environment stopped;
start it once more through the up script when the caller needs a running app.
Never exercise against a developer-owned service or a shared environment. A
read-only descriptor pass is not a substitute for these lifecycle tests.

Also test one real source/build-input change using the project's existing test
surface. Preserve the user's file contents and restore only the test's own change.
Verify that the input invalidates reuse/cache, rather than permanently forcing all
builds. For containers, test ownership and teardown with project-specific fixtures;
a process-only test does not prove service cleanup. Record the commands, timings,
platform, and uncovered cases in the generation report.

The forced-rebuild exercise proves that the old app is replaced, not that its
preparation actually ran. Verify a real build/install output or invocation in the
recipe's own test while the environment is healthy. Also invoke the up command
directly with controlled failures after resources are created (for example,
database readiness and app start), and with an interruption where supported.
Before any rescue teardown, assert that owned processes, containers, disposable
volumes and locks are gone and borrowed resources survive. The checker's fallback
cleanup must not hide a broken up-script cleanup path. Keep fault injection in
disposable fixtures; never break a developer's existing database to test this.
Verify the browser-to-API readiness proof and credential propagation described in
`references/project-runtime.md` for the actual recipe, or report their limits.

A missing Node runtime, unsupported command flavor, failed lifecycle check, or
unverified required browser policy leaves generation incomplete. Fix the relevant
script and repeat the affected test; do not silently skip a case or report a
portable PASS from a test run on one platform. The helper's fixture suite is
`node scripts/test-test-env-contract.mjs` in the collection source; it tests the
helper, not a consumer application's generated environment.
