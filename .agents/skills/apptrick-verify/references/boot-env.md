# Boot the app via apptrick-prepare-test-env

Detailed procedure for step 7 of `apptrick-verify`. Do not boot the app by hand. Invoke the `apptrick-prepare-test-env` skill (mode `auto`; pass `--no-ephemeral` when the app clearly needs no backing services). It discovers or provisions a runnable instance, installs the configured browser provider when missing, and writes the environment descriptor. Then read the descriptor:

```bash
QA_DIR=$(jq -r '.paths.qa // ".ai/qa"' .ai/agentic.config.json 2>/dev/null || echo ".ai/qa")
ENV_DESCRIPTOR="$QA_DIR/test-env.json"
BASE_URL=$(jq -r '.baseUrl' "$ENV_DESCRIPTOR")
BROWSER_PROVIDER=$(jq -r '.browser.provider // (if .playwright.runner then "playwright" else empty end) // "playwright"' "$ENV_DESCRIPTOR")
case "$BROWSER_PROVIDER" in
  ''|*[!A-Za-z0-9._-]*) echo "Invalid browser provider in $ENV_DESCRIPTOR: $BROWSER_PROVIDER" >&2; exit 1 ;;
esac
BROWSER_FILE=".ai/browsers/${BROWSER_PROVIDER}.md"
BROWSER_COMMAND=$(jq -r '.browser.command // .playwright.runner // empty' "$ENV_DESCRIPTOR")
if [ "$BROWSER_PROVIDER" = "agent-browser" ] && [ -n "$BROWSER_COMMAND" ]; then
  AGENT_BROWSER_BIN="$BROWSER_COMMAND"
fi
BROWSER_INSTALLED=$(jq -r '.browser.installed // .playwright.installed // false' "$ENV_DESCRIPTOR")
```

Read `$BROWSER_FILE` and execute its named operations using the descriptor-selected
command for every call. On PowerShell bind `$AgentBrowser = $BrowserCommand`
after reading `browser.command`. Never fall back to a raw PATH/cache executable
when the descriptor records a wrapper; a missing or unusable wrapper blocks
browser QA until `apptrick-prepare-test-env` repairs it. Keep this binding for open,
snapshot, interact, assert, screenshot, and close, even in a later invocation. An older descriptor may
lack `browser`; in that case use the legacy Playwright object and embedded
Playwright flow. An explicit non-Playwright provider without a descriptor is a
setup error - invoke `apptrick-set-up` to install it, then retry.

Before login or evidence capture, validate the effective UI and API targets
against the authorized environment, including redirects. A local-only recipe
requires loopback; deployed QA uses its explicitly approved target scope. An
arbitrary URL override is not permission to send credentials there. Keep package
resolution tokens out of browser/test processes and load only the demo/runtime
variables this scenario needs.

Record whether this run started the env (so the final step tears down only what it
created - reuse the descriptor's `startedByThisRepo`). Pick the login role whose
access actually covers the changed surface from the descriptor's `credentials`,
and note the chosen role in the report. Credentials are references: load the
descriptor's `credentialsFile` into the shell (`set -a; . "$CREDENTIALS_FILE";
set +a`) and write the entry's `passwordEnv` reference literally in login
commands - `"$TEST_ADMIN_PASSWORD"`, expanded by the shell - never read
`credentialsFile` into your context or restate a password value. A legacy
descriptor with inline values is passed through the runner's environment the
same way, without quoting them back. If `apptrick-prepare-test-env` reports the app
could not boot or browsers could not be installed, do **not** fabricate results:
record the environment blocker in the report honestly, post/save it, and release
the lock.
