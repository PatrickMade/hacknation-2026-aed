#!/usr/bin/env node

import { execFileSync, spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";

class ContractError extends Error {}

function parseArgs(argv) {
  const result = {
    descriptor: ".ai/qa/test-env.json",
    ttlSeconds: Number(process.env.TEST_ENV_CACHE_TTL_SECONDS || 600),
    exerciseTtlSeconds: 1,
    commandTimeoutSeconds: 300,
    exercise: false,
    allowedDomains: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const name = argv[index];
    if (name === "--exercise") result.exercise = true;
    else if (name === "--allowed-domain") result.allowedDomains.push(argv[++index]);
    else if (["--project-root", "--descriptor"].includes(name)) {
      result[name.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = argv[++index];
    } else if (name === "--ttl-seconds") result.ttlSeconds = Number(argv[++index]);
    else if (name === "--exercise-ttl-seconds") result.exerciseTtlSeconds = Number(argv[++index]);
    else if (name === "--command-timeout-seconds") result.commandTimeoutSeconds = Number(argv[++index]);
    else throw new ContractError(`unknown argument ${name}`);
  }
  if (!result.projectRoot) throw new ContractError("--project-root is required");
  if (!Number.isFinite(result.ttlSeconds) || result.ttlSeconds <= 0) throw new ContractError("--ttl-seconds must be positive");
  if (!Number.isFinite(result.exerciseTtlSeconds) || result.exerciseTtlSeconds <= 0 || result.exerciseTtlSeconds > 10) {
    throw new ContractError("--exercise-ttl-seconds must be greater than 0 and at most 10");
  }
  if (!Number.isFinite(result.commandTimeoutSeconds) || result.commandTimeoutSeconds < 1 || result.commandTimeoutSeconds > 1800) {
    throw new ContractError("--command-timeout-seconds must be between 1 and 1800");
  }
  return result;
}

function requireValue(condition, message) {
  if (!condition) throw new ContractError(message);
}

function scopedPath(root, value, label, mustExist = true) {
  requireValue(typeof value === "string" && value.length > 0 && !value.includes("\0"), `${label} must be a non-empty path`);
  const target = resolve(root, value);
  if (mustExist) {
    requireValue(existsSync(target), `${label} does not exist`);
    const real = realpathSync(target);
    const realRel = relative(root, real);
    requireValue(realRel === "" || (!realRel.startsWith("..") && !isAbsolute(realRel)), `${label} resolves outside the project root`);
    return real;
  }
  const rel = relative(root, target);
  requireValue(rel === "" || (!rel.startsWith("..") && !isAbsolute(rel)), `${label} must stay inside the project root`);
  return target;
}

function parseDescriptor(path) {
  let value;
  try {
    value = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    if (error instanceof SyntaxError) throw new ContractError("descriptor is not valid JSON");
    throw new ContractError("descriptor could not be read");
  }
  requireValue(value && typeof value === "object" && !Array.isArray(value), "descriptor root must be an object");
  return value;
}

function alive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function sha256(text) {
  return createHash("sha256").update(text).digest("hex");
}

function validateBrowser(root, value, allowedDomains) {
  if (!value.browser) {
    if (value.playwright !== undefined) {
      requireValue(value.playwright && typeof value.playwright === "object", "playwright must be an object");
      requireValue(value.playwright.runner === "playwright", "playwright.runner must be playwright");
      requireValue(typeof value.playwright.installed === "boolean", "playwright.installed must be boolean");
    }
    return { provider: "legacy-playwright", policy: "not-applicable" };
  }

  const browser = value.browser;
  requireValue(browser && typeof browser === "object" && !Array.isArray(browser), "browser must be an object");
  requireValue(typeof browser.provider === "string" && /^[A-Za-z0-9._-]+$/.test(browser.provider), "browser.provider is invalid");
  requireValue(typeof browser.installed === "boolean", "browser.installed must be boolean");
  requireValue(typeof browser.version === "string", "browser.version must be a string");
  requireValue(typeof browser.notes === "string", "browser.notes must be a string");
  if (!browser.installed) return { provider: browser.provider, policy: "not-applicable" };
  requireValue(typeof browser.command === "string" && browser.command.length > 0 && !/[\r\n\0]/.test(browser.command), "browser.command must name one executable");

  if (browser.provider !== "agent-browser") return { provider: browser.provider, policy: "not-applicable" };
  if (allowedDomains.length === 0) return { provider: browser.provider, policy: "not-verified" };
  requireValue(new Set(allowedDomains).size === allowedDomains.length, "--allowed-domain values must be unique");
  const wrapper = scopedPath(root, browser.command, "browser.command");
  requireValue(lstatSync(wrapper).isFile(), "browser.command must be a file");
  const policyPath = `${wrapper}.policy.json`;
  requireValue(existsSync(policyPath), "agent-browser command must be the generated policy wrapper");
  let policy;
  try {
    policy = JSON.parse(readFileSync(policyPath, "utf8"));
  } catch {
    throw new ContractError("generated browser wrapper policy is invalid");
  }
  requireValue(policy.version === 1, "generated browser wrapper policy version is unsupported");
  requireValue(Array.isArray(policy.allowedDomains), "generated browser wrapper policy has no allowedDomains");
  requireValue(JSON.stringify(policy.allowedDomains) === JSON.stringify(allowedDomains), "generated browser wrapper domains differ from the approved list");
  requireValue(sha256(readFileSync(wrapper)) === policy.wrapperSha256, "generated browser wrapper does not match its policy hash");
  requireValue(typeof policy.browserExecutable === "string" && existsSync(policy.browserExecutable), "generated browser wrapper target is missing");
  const configPath = scopedPath(root, policy.configPath, "generated browser wrapper safe config");
  requireValue(sha256(readFileSync(configPath)) === policy.configSha256, "generated browser wrapper safe config does not match its policy hash");
  return { provider: browser.provider, policy: "verified" };
}

function validateDescriptor(root, descriptorPath, ttlSeconds, allowedDomains) {
  const value = parseDescriptor(descriptorPath);
  requireValue(value.version === 1, "descriptor.version must be 1");
  requireValue(typeof value.runId === "string" && value.runId.length > 0, "descriptor.runId must be a non-empty string");
  requireValue(["running", "stopped"].includes(value.status), "descriptor.status must be running or stopped");
  requireValue(["discovered", "ephemeral", "dev", "docker", "prod"].includes(value.mode), "descriptor.mode is unsupported");
  requireValue(typeof value.baseUrl === "string", "descriptor.baseUrl must be a string");
  try {
    const url = new URL(value.baseUrl);
    requireValue(["http:", "https:"].includes(url.protocol) && Boolean(url.hostname), "descriptor.baseUrl must be an HTTP(S) URL");
  } catch (error) {
    if (error instanceof ContractError) throw error;
    throw new ContractError("descriptor.baseUrl must be an HTTP(S) URL");
  }
  requireValue(typeof value.startedByThisRepo === "boolean", "descriptor.startedByThisRepo must be boolean");
  const startScript = scopedPath(root, value.startScript, "descriptor.startScript");
  const stopScript = scopedPath(root, value.stopScript, "descriptor.stopScript");
  requireValue(/\.(?:sh|ps1)$/.test(startScript) && /\.(?:sh|ps1)$/.test(stopScript), "entrypoints must be .sh or .ps1 files");
  requireValue(startScript.endsWith(".sh") === stopScript.endsWith(".sh"), "start and stop entrypoints must use the same shell flavor");
  requireValue(value.app && typeof value.app === "object" && !Array.isArray(value.app), "descriptor.app must be an object");
  requireValue(typeof value.app.startCommand === "string", "descriptor.app.startCommand must be a string");
  requireValue(Number.isInteger(value.app.port) && value.app.port >= 1 && value.app.port <= 65535, "descriptor.app.port must be a valid port");
  requireValue(typeof value.app.healthPath === "string" && value.app.healthPath.startsWith("/"), "descriptor.app.healthPath must start with /");
  requireValue(Number.isInteger(value.app.pid) && value.app.pid > 0, "descriptor.app.pid must be a positive integer");
  requireValue(Array.isArray(value.services), "descriptor.services must be an array");
  if (value.credentials !== undefined) requireValue(Array.isArray(value.credentials), "descriptor.credentials must be an array");
  if (value.credentialsFile !== undefined) scopedPath(root, value.credentialsFile, "descriptor.credentialsFile", false);
  requireValue(["linux", "darwin", "wsl2", "win32"].includes(value.platform), "descriptor.platform is unsupported");
  const startedAt = Date.parse(value.startedAt);
  requireValue(Number.isFinite(startedAt), "descriptor.startedAt must be an ISO-8601 timestamp");
  if (value.status === "running") {
    const ageSeconds = (Date.now() - startedAt) / 1000;
    requireValue(ageSeconds >= -5, "descriptor.startedAt is in the future");
    requireValue(ageSeconds <= ttlSeconds, `running descriptor age ${Math.floor(ageSeconds)}s exceeds TTL ${ttlSeconds}s`);
    if (value.startedByThisRepo) requireValue(alive(value.app.pid), "owned running descriptor PID is not alive");
  }
  if (value.testRunner !== undefined) {
    requireValue(value.testRunner && typeof value.testRunner === "object", "descriptor.testRunner must be an object");
    requireValue(["playwright", "cypress", "wdio", "other", "none"].includes(value.testRunner.name), "descriptor.testRunner.name is unsupported");
  }
  const provider = validateBrowser(root, value, allowedDomains);
  return { value, startScript, stopScript, provider };
}

function commandFor(script) {
  if (script.endsWith(".sh")) return { executable: "sh", args: [script] };
  const candidates = process.platform === "win32" ? ["pwsh", "powershell"] : ["pwsh"];
  for (const executable of candidates) {
    const probe = spawnSync(executable, ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"], { stdio: "ignore", shell: false });
    if (!probe.error && probe.status === 0) return { executable, args: ["-NoProfile", "-File", script] };
  }
  throw new ContractError("PowerShell entrypoint cannot be exercised because pwsh/powershell is unavailable");
}

function runEntrypoint(root, script, timeoutSeconds, environment = {}, args = []) {
  const command = commandFor(script);
  try {
    execFileSync(command.executable, [...command.args, ...args], {
      env: { ...process.env, ...environment },
      cwd: root,
      stdio: "pipe",
      encoding: "utf8",
      shell: false,
      timeout: timeoutSeconds * 1000,
      maxBuffer: 1024 * 1024,
    });
  } catch (error) {
    const status = error.status === null || error.status === undefined ? "unavailable" : error.status;
    throw new ContractError(`entrypoint ${script.endsWith(".sh") ? "sh" : "PowerShell"} execution failed (status ${status})`);
  }
}

async function waitFor(predicate, timeoutMs = 2_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return true;
    await new Promise((resolveWait) => setTimeout(resolveWait, 25));
  }
  return predicate();
}

async function terminate(pid) {
  if (!alive(pid)) return;
  try { process.kill(pid, "SIGTERM"); } catch {}
  if (await waitFor(() => !alive(pid), 1_000)) return;
  try { process.kill(pid, "SIGKILL"); } catch {}
  await waitFor(() => !alive(pid), 1_000);
}

async function exercise(root, descriptorPath, options, initial) {
  const ttlEnvironment = { TEST_ENV_CACHE_TTL_SECONDS: String(options.exerciseTtlSeconds) };
  const forceTtlSeconds = options.commandTimeoutSeconds + 10;
  let activePid = null;
  let activeOwned = null;
  let previousOwned = null;
  let sentinel = null;
  let forged = false;
  let stoppedBackup = null;
  let primaryError = null;
  let cleanupError = null;
  let lifecycleStarted = false;
  try {
    requireValue(initial.value.startedByThisRepo, "exercise refuses an initial descriptor not owned by this repository");
    runEntrypoint(root, initial.stopScript, options.commandTimeoutSeconds, ttlEnvironment);
    lifecycleStarted = true;
    runEntrypoint(root, initial.startScript, options.commandTimeoutSeconds, ttlEnvironment);
    const cold = validateDescriptor(root, descriptorPath, options.exerciseTtlSeconds, options.allowedDomains);
    requireValue(cold.value.status === "running" && cold.value.startedByThisRepo, "cold entrypoint did not create an owned running environment");
    activePid = cold.value.app.pid;

    runEntrypoint(root, cold.startScript, options.commandTimeoutSeconds, ttlEnvironment);
    const warm = validateDescriptor(root, descriptorPath, options.exerciseTtlSeconds, options.allowedDomains);
    requireValue(warm.value.runId === cold.value.runId && warm.value.app.pid === cold.value.app.pid, "warm entrypoint did not reuse the same environment identity");

    previousOwned = warm.value;
    runEntrypoint(root, warm.startScript, options.commandTimeoutSeconds, { TEST_ENV_CACHE_TTL_SECONDS: String(forceTtlSeconds) }, ["--force-rebuild"]);
    const forced = validateDescriptor(root, descriptorPath, forceTtlSeconds, options.allowedDomains);
    activePid = forced.value.app.pid;
    activeOwned = forced.value;
    requireValue(forced.value.status === "running" && forced.value.startedByThisRepo && forced.value.runId !== warm.value.runId && forced.value.app.pid !== warm.value.app.pid, "force-rebuild did not restart the environment identity");
    requireValue(await waitFor(() => !alive(warm.value.app.pid)), "force-rebuild left the previous app PID alive");
    previousOwned = null;
    activeOwned = null;

    await new Promise((resolveWait) => setTimeout(resolveWait, Math.ceil(options.exerciseTtlSeconds * 1000) + 150));
    runEntrypoint(root, forced.startScript, options.commandTimeoutSeconds, ttlEnvironment);
    const restarted = validateDescriptor(root, descriptorPath, options.exerciseTtlSeconds, options.allowedDomains);
    requireValue(restarted.value.runId !== forced.value.runId && restarted.value.app.pid !== forced.value.app.pid, "TTL expiry did not restart the environment identity");
    requireValue(await waitFor(() => !alive(forced.value.app.pid)), "TTL restart left the previous app PID alive");
    activePid = restarted.value.app.pid;

    runEntrypoint(root, restarted.stopScript, options.commandTimeoutSeconds, ttlEnvironment);
    runEntrypoint(root, restarted.stopScript, options.commandTimeoutSeconds, ttlEnvironment);
    const stopped = validateDescriptor(root, descriptorPath, options.ttlSeconds, options.allowedDomains);
    requireValue(stopped.value.status === "stopped", "double teardown did not leave a stopped descriptor");
    requireValue(await waitFor(() => !alive(restarted.value.app.pid)), "teardown left the app PID alive");
    activePid = null;
    lifecycleStarted = false;

    sentinel = spawn(process.execPath, ["-e", "setInterval(() => {}, 1000)"], { detached: true, stdio: "ignore" });
    sentinel.unref();
    stoppedBackup = readFileSync(descriptorPath, "utf8");

    for (const declaredOwned of [false, true]) {
      for (const expired of [false, true]) {
        const forgedValue = {
          ...stopped.value,
          status: "running",
          startedByThisRepo: declaredOwned,
          startedAt: expired
            ? new Date(Date.now() - ((options.exerciseTtlSeconds + 2) * 1000)).toISOString()
            : new Date().toISOString(),
          services: [],
          app: { ...stopped.value.app, pid: sentinel.pid },
        };
        writeFileSync(descriptorPath, `${JSON.stringify(forgedValue, null, 2)}\n`);
        forged = true;
        let candidatePid = null;
        let upError = null;
        let forgedCleanupError = null;
        try {
          runEntrypoint(root, stopped.startScript, options.commandTimeoutSeconds, ttlEnvironment);
          const afterUp = parseDescriptor(descriptorPath);
          if (afterUp?.app?.pid !== sentinel.pid && Number.isInteger(afterUp?.app?.pid)) candidatePid = afterUp.app.pid;
          const sentinelExited = await waitFor(() => sentinel.exitCode !== null || !alive(sentinel.pid), 250);
          requireValue(!sentinelExited, `${expired ? "expired " : ""}forged up entrypoint killed an unrelated sentinel PID`);
          requireValue(afterUp?.app?.pid !== sentinel.pid, "forged up entrypoint adopted an unrelated sentinel PID");
          requireValue(afterUp.status === "running" && afterUp.startedByThisRepo === true && alive(afterUp.app.pid), "forged up entrypoint did not establish a distinct owned environment");
        } catch (error) {
          upError = error;
        } finally {
          try {
            runEntrypoint(root, stopped.stopScript, options.commandTimeoutSeconds, ttlEnvironment);
          } catch (error) {
            forgedCleanupError = error;
          }
          if (candidatePid !== null && !(await waitFor(() => !alive(candidatePid)))) {
            forgedCleanupError = new ContractError("reviewed teardown did not clean up the forged-up replacement environment");
          }
          const sentinelExitedDuringCleanup = await waitFor(() => sentinel.exitCode !== null || !alive(sentinel.pid), 250);
          if (sentinelExitedDuringCleanup) {
            forgedCleanupError = new ContractError("reviewed forged-up cleanup killed the unrelated sentinel PID");
          }
          writeFileSync(descriptorPath, stoppedBackup);
          forged = false;
        }
        if (upError && forgedCleanupError) {
          throw new ContractError(`${upError.message}; forged-up cleanup failed: ${forgedCleanupError.message}`);
        }
        if (forgedCleanupError) throw forgedCleanupError;
        if (upError) throw upError;
      }
    }

    for (const declaredOwned of [false, true]) {
      const forgedValue = {
        ...stopped.value,
        status: "running",
        startedByThisRepo: declaredOwned,
        startedAt: new Date().toISOString(),
        services: [],
        app: { ...stopped.value.app, pid: sentinel.pid },
      };
      writeFileSync(descriptorPath, `${JSON.stringify(forgedValue, null, 2)}\n`);
      forged = true;
      runEntrypoint(root, stopped.stopScript, options.commandTimeoutSeconds, ttlEnvironment);
      const sentinelExited = await waitFor(() => sentinel.exitCode !== null || !alive(sentinel.pid), 250);
      requireValue(!sentinelExited, `teardown killed an unrelated sentinel process from a forged startedByThisRepo:${declaredOwned} descriptor`);
      writeFileSync(descriptorPath, stoppedBackup);
      forged = false;
    }
  } catch (error) {
    primaryError = error;
  } finally {
    if (forged && stoppedBackup !== null) writeFileSync(descriptorPath, stoppedBackup);
    if (lifecycleStarted) {
      const cleanupFailures = [];
      try { runEntrypoint(root, initial.stopScript, options.commandTimeoutSeconds, ttlEnvironment); } catch (error) { cleanupFailures.push(error.message); }
      if (previousOwned && !(await waitFor(() => !alive(previousOwned.app.pid), 250))) {
        let latestDescriptor = null;
        try {
          if (existsSync(descriptorPath)) latestDescriptor = readFileSync(descriptorPath, "utf8");
          writeFileSync(descriptorPath, `${JSON.stringify(previousOwned, null, 2)}\n`);
          runEntrypoint(root, initial.stopScript, options.commandTimeoutSeconds, ttlEnvironment);
        } catch (error) { cleanupFailures.push(`previous app teardown failed: ${error.message}`); }
        finally {
          // Keep the replacement's recovery state if its teardown failed.
          if (latestDescriptor !== null && !alive(previousOwned.app.pid)) {
            try { writeFileSync(descriptorPath, latestDescriptor); }
            catch (error) { cleanupFailures.push("could not restore the current environment descriptor"); }
          }
        }
      }
      if (previousOwned && activeOwned && activePid !== previousOwned.app.pid && alive(previousOwned.app.pid) && alive(activePid)) {
        const recoveryContents = `${JSON.stringify(activeOwned, null, 2)}\n`;
        const recoveryPath = `${descriptorPath}.recovery-${sha256(recoveryContents)}.json`;
        try {
          try { writeFileSync(recoveryPath, recoveryContents, { flag: "wx", mode: 0o600 }); }
          catch (error) {
            if (error.code !== "EEXIST" || !lstatSync(recoveryPath).isFile() || readFileSync(recoveryPath, "utf8") !== recoveryContents) throw error;
          }
          cleanupFailures.push(`replacement recovery descriptor: ${relative(root, recoveryPath)}`);
        } catch { cleanupFailures.push("could not preserve the replacement recovery descriptor"); }
      }
      if (activePid !== null && !(await waitFor(() => !alive(activePid)))) cleanupFailures.push("reviewed teardown did not confirm cleanup of the active app PID");
      if (previousOwned && !(await waitFor(() => !alive(previousOwned.app.pid)))) cleanupFailures.push("reviewed teardown did not confirm cleanup of the previous app PID");
      if (cleanupFailures.length > 0) cleanupError = new ContractError(cleanupFailures.join("; "));
    }
    if (sentinel) await terminate(sentinel.pid);
  }
  if (primaryError && cleanupError) {
    throw new ContractError(`${primaryError.message}; cleanup failed: ${cleanupError.message}`);
  }
  if (primaryError) throw primaryError;
  if (cleanupError) throw cleanupError;
}

try {
  const options = parseArgs(process.argv.slice(2));
  const root = realpathSync(resolve(options.projectRoot));
  const descriptorPath = scopedPath(root, options.descriptor, "descriptor");
  const validated = validateDescriptor(root, descriptorPath, options.ttlSeconds, options.allowedDomains);
  process.stdout.write(`TEST_ENV_CHECK=pass\nTEST_ENV_DESCRIPTOR=${relative(root, descriptorPath)}\nTEST_ENV_BROWSER_POLICY=${validated.provider.policy}\nTEST_ENV_RUNTIME_PROOF=${options.exercise ? "pending" : "not-exercised"}\n`);
  if (options.exercise) {
    await exercise(root, descriptorPath, options, validated);
    process.stdout.write("TEST_ENV_EXERCISE=pass\n");
  }
} catch (error) {
  const message = error instanceof ContractError ? error.message : "unexpected checker failure";
  process.stderr.write(`Test environment contract failed: ${message}\n`);
  process.exitCode = 1;
}
