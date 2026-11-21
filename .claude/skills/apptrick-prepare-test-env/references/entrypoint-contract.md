# The entrypoint contract - what the up script must implement

The full contract the generated up/down scripts must satisfy. Called from the
`apptrick-prepare-test-env` body during Phase 2 step 2.3 (write the scripts); the fast
path (Phase 1) only runs the resulting script and never needs this file.

The generated script is self-sufficient: everything this skill used to do per
run now happens inside it, with no agent reasoning at run time. The contract is
flavor-independent - the steps below are shown as POSIX `sh`; the PowerShell
flavor implements the identical sequence with the equivalents listed at the end
of this section. In order:

1. **Marker + parameters.** First lines after the shebang:

   ```sh
   #!/bin/sh
   # apptrick-prepare-test-env: generated entrypoint (contract v2)
   # regenerate with: apptrick-prepare-test-env --regenerate
   # history:
   #   <ISO date> generated (cold 184s, warm 3s)
   #   <ISO date> repair: wait for redis before migrate (fixes race on fresh boot)
   set -eu
   ```

   PowerShell flavor of the same header (no shebang; strict mode instead of
   `set -eu`):

   ```powershell
   # apptrick-prepare-test-env: generated entrypoint (contract v2)
   # regenerate with: apptrick-prepare-test-env --regenerate
   # history:
   #   <ISO date> generated (cold 184s, warm 3s)
   Set-StrictMode -Version Latest
   $ErrorActionPreference = 'Stop'
   ```

   The `# history:` header is the script's changelog: every generation and
   every repair appends one dated line saying what changed and which failure it
   prevents. It is how a future run (or a human) can tell why the script looks
   the way it does.

   Then a single block of project-specific variables (launch command, prep
   chain, service images, preferred port, build inputs/artifacts/env-vars,
   TTL) so tweaks never require touching the logic below. Flags: `--force`,
   `--force-rebuild`; env override `TEST_ENV_CACHE_TTL_SECONDS` (default ~600).
   `--force-rebuild` bypasses both healthy reuse and the build cache: stop owned
   processes consuming those artifacts, run the full preparation/build chain,
   then start a fresh environment identity. It must not rebuild under a running
   consumer. Do not restart a borrowed service owned by another checkout.

2. **Lock - one bootstrap at a time.** Directory lock at `$QA_DIR/test-env.lock`
   (`mkdir` is atomic) holding `owner.json` `{pid, source, acquiredAt}`. Owner
   PID dead → stale, remove and retake. Owner alive → bounded poll-wait
   (~5 min), then re-check the descriptor - the other process likely produced a
   reusable environment. Release on every exit path (`trap`). When the app
   serves from in-repo build artifacts, hold the lock for the environment's
   lifetime so a second bootstrap cannot rebuild artifacts under a running app.

3. **Reuse check - attach, don't reboot.** If the descriptor says
   `"status":"running"`, reuse only when **all** pass (a state file is a claim,
   not proof): recorded PID alive (`kill -0`) and process start identity plus checkout/run ownership match (a reused PID must never be attached to or killed); real readiness probes with
   bounded timeouts at increasing depth (app shell → unauthenticated API →
   one authenticated round trip when credentials are recorded - the script
   sources `credentialsFile` itself, so password values stay inside the script
   run; the deep probes catch an app that lost its database); fresh (age
   within TTL **and** no
   tracked source file newer than `startedAt`). All pass → finalize through step 7,
   including its readiness evidence and descriptor checks, then exit 0 (unless
   `--force` or `--force-rebuild`). Any failure → treat as stale, tear down what
   this repo started, continue.

4. **Build cache - skip preparation that has not changed.** The generic
   mechanism in `references/build-cache.md`. Fingerprint match and artifacts
   present → skip install/
   codegen/build entirely; otherwise run the full preparation chain and write a
   fresh cache entry.

5. **Services up (ephemeral mode).** Start each backing service as a disposable
   Docker container on `127.0.0.1:<port>` - stable preferred port when free,
   otherwise a fresh free port:

   ```sh
   # Never assume python3 exists - cascade through whatever the machine has,
   # and fall back to a random high port (the caller retries on bind failure).
   free_port() {
     if command -v python3 >/dev/null 2>&1; then
       python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'
     elif command -v python >/dev/null 2>&1; then
       python -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'
     elif command -v node >/dev/null 2>&1; then
       node -e 's=require("net").createServer();s.listen(0,"127.0.0.1",()=>{console.log(s.address().port);s.close()})'
     else
       awk 'BEGIN{srand();print 20000+int(rand()*20000)}'
     fi
   }
   ```

   PowerShell flavor - no external interpreter needed:

   ```powershell
   function Get-FreePort {
     $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
     $l.Start(); $port = $l.LocalEndpoint.Port; $l.Stop(); $port
   }
   ```

   Throwaway names/volumes (`--rm`, anonymous volumes), official images at the
   repo's pinned versions. Poll each service until it accepts connections -
   never race the app ahead of its database. Export the connection env the app
   expects, then run the repo's own migrate/seed command (never hand-written
   SQL). In discovered mode, this step is replaced by the repo's own up-command
   with its own flags.

6. **App start + health wait.** Launch in the background, record the PID, poll
   the base URL until healthy (bounded), resolve the real bound port.

7. **Descriptor write + output.** Write `$ENV_DESCRIPTOR` and the
   `credentialsFile` env file beside it (full schema and the
   credential-reference contract in `references/env-descriptor.md`), ensure the
   env file is covered by `.gitignore` (append the entry when missing), and
   run the read-only checker from `references/verification.md` with the effective TTL and browser policy on every success path (cold and warm), then print machine-readable result lines consumers can grep:

   ```
   TEST_ENV_STATUS=running
   TEST_ENV_BASE_URL=http://127.0.0.1:4321
   TEST_ENV_DESCRIPTOR=.ai/qa/test-env.json
   TEST_ENV_REUSED=1        # 0 on a fresh boot
   BROWSER_PROVIDER=agent-browser
   BROWSER_INSTALLED=1
   ```

   Preserve the provider state verified during generation. The warm entrypoint
   does not reinstall it; when **doctor** later fails, return to generation in
   repair mode and repair the provider installation through its descriptor.

   For a connected UI/API recipe, bake the representative browser-to-API probe
   into every success path, including reuse. Reuse its last successful evidence
   only while its connection/config fingerprint and required service run
   identities still match; otherwise run the probe before claiming connected
   readiness. Save the binding/result as ignored recipe evidence and reference
   it in descriptor `notes`. Old scripts without this proof need repair. When
   the probe is unavailable or fails, keep any safely running services available
   but record the missing/failed proof in `notes` and report degraded integration,
   never an end-to-end PASS. Static/API-only recipes record it as inapplicable.

The down script (`test-env-down.sh` / `test-env-down.ps1`) mirrors it: stop the
app only after independently verifying process start identity and checkout/run ownership; never trust the descriptor PID alone. Remove exactly the
containers/volumes the up script created (scoped by the throwaway names), mark
the descriptor `"status":"stopped"`. Safe to run twice; never touches anything
it did not create.

The up script also owns cleanup on failed or interrupted startup, without an
external checker calling down afterward. Record owned resources as they are
created, before readiness or descriptor validation can fail. On failure, INT or
TERM, release the lock and stop/remove only those processes, containers and
disposable volumes; preserve reused services and data. Cleanup must work when the
descriptor is missing or incomplete. Preserve the original failure and report any
cleanup failure as well; do not turn either into a successful start.

When generating the PowerShell flavor, use these equivalents for the
contract's primitives (Docker commands are identical in both):

| Contract primitive | POSIX `sh` | PowerShell |
| --- | --- | --- |
| Fail fast on errors | `set -eu` | `Set-StrictMode -Version Latest; $ErrorActionPreference='Stop'` |
| Atomic lock | `mkdir "$QA_DIR/test-env.lock"` | `New-Item -ItemType Directory $LockDir` (throws when it exists) |
| Release on every exit | `trap ... EXIT` | `try { … } finally { … }` |
| PID alive? | `kill -0 "$PID"` | `Get-Process -Id $appPid -ErrorAction SilentlyContinue` (never name the variable `$PID` - it is a read-only automatic in PowerShell) |
| Background app start | `cmd &` + `$!` | `Start-Process -PassThru` (keep `.Id`) |
| HTTP health probe | `curl -fsS` / `wget -q` | `Invoke-WebRequest -UseBasicParsing -TimeoutSec …` |
| UTC timestamp | `date -u +%FT%TZ` | `(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')` |
| File size+mtime | `stat -f '%z:%m'` / `stat -c '%s:%Y'` | `"$($_.Length):$($_.LastWriteTimeUtc.Ticks)"` from `Get-ChildItem` |
| Checksum for fingerprint | `cksum` | `Get-FileHash -Algorithm SHA256 -InputStream` over the joined string |
| JSON read/write | `jq` / `sed` fallback | `ConvertFrom-Json` / `ConvertTo-Json` (built in) |
| Free port | `free_port()` cascade above | `Get-FreePort` above |
