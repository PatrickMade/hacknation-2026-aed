#!/usr/bin/env node

import { createHash, randomBytes } from "node:crypto";
import {
  closeSync,
  constants,
  fchmodSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  realpathSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";

function fail(message) {
  process.stderr.write(`Browser wrapper generation failed: ${message}\n`);
  process.exit(1);
}

function parseArgs(argv) {
  const result = { allowedDomains: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const name = argv[index];
    if (name === "--allowed-domain") {
      result.allowedDomains.push(argv[++index]);
    } else if (["--project-root", "--output", "--browser-executable"].includes(name)) {
      result[name.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = argv[++index];
    } else {
      fail(`unknown argument ${name}`);
    }
  }
  return result;
}

function inside(root, target, label) {
  const rel = relative(root, target);
  if (rel === "" || (!rel.startsWith("..") && !isAbsolute(rel))) return target;
  fail(`${label} must stay inside the project root`);
}

function lexicalStat(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function checkOutputAncestors(root, output) {
  const parentRelative = relative(root, dirname(output));
  let current = root;
  for (const part of parentRelative === "" ? [] : parentRelative.split(sep)) {
    current = resolve(current, part);
    const stat = lexicalStat(current);
    if (!stat) break;
    if (stat.isSymbolicLink()) fail(`wrapper output ancestor is a symlink: ${relative(root, current)}`);
    if (!stat.isDirectory()) fail(`wrapper output ancestor is not a directory: ${relative(root, current)}`);
  }
}

function atomicWrite(path, contents, mode) {
  const temporary = `${path}.tmp-${randomBytes(16).toString("hex")}`;
  const noFollow = constants.O_NOFOLLOW || 0;
  let descriptor;
  let created = false;
  try {
    descriptor = openSync(temporary, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | noFollow, mode);
    created = true;
    writeFileSync(descriptor, contents);
    fchmodSync(descriptor, mode);
    closeSync(descriptor);
    descriptor = undefined;
    renameSync(temporary, path);
  } catch (error) {
    if (descriptor !== undefined) closeSync(descriptor);
    if (created) {
      try { unlinkSync(temporary); } catch {}
    }
    throw error;
  }
}

function validDomain(value) {
  return typeof value === "string"
    && value.length > 0
    && value.length <= 253
    && !/[\s,/:\\]/.test(value)
    && value !== "*"
    && /^(?:\*\.)?(?:localhost|(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*|\d{1,3}(?:\.\d{1,3}){3})$/.test(value);
}

const args = parseArgs(process.argv.slice(2));
if (!args.projectRoot || !args.output || !args.browserExecutable) fail("--project-root, --output, and --browser-executable are required");
if (args.allowedDomains.length === 0) fail("at least one --allowed-domain is required");
for (const domain of args.allowedDomains) if (!validDomain(domain)) fail(`invalid allowed domain ${JSON.stringify(domain)}`);
if (new Set(args.allowedDomains).size !== args.allowedDomains.length) fail("allowed domains must be unique");

const projectRoot = realpathSync(resolve(args.projectRoot));
const output = inside(projectRoot, resolve(projectRoot, args.output), "wrapper output");
const browserExecutable = realpathSync(resolve(args.browserExecutable));
if (!lstatSync(browserExecutable).isFile()) fail("browser executable is not a file");
checkOutputAncestors(projectRoot, output);
for (const path of [output, `${output}.config.json`, `${output}.policy.json`]) {
  const stat = lexicalStat(path);
  if (stat?.isSymbolicLink()) fail(`refusing to replace a symlinked wrapper artifact: ${relative(projectRoot, path)}`);
  if (stat && !stat.isFile()) fail(`refusing to replace a non-file wrapper artifact: ${relative(projectRoot, path)}`);
}
mkdirSync(dirname(output), { recursive: true });
checkOutputAncestors(projectRoot, output);
inside(projectRoot, realpathSync(dirname(output)), "wrapper output directory");

const safeConfig = `${output}.config.json`;
const policyPath = `${output}.policy.json`;
const safeConfigText = "{}\n";
const priorArtifacts = [output, safeConfig, policyPath].filter((path) => lexicalStat(path));
if (priorArtifacts.length > 0) {
  if (priorArtifacts.length !== 3) fail("refusing to overwrite an incomplete or non-generator-owned wrapper artifact set");
  try {
    const priorPolicy = JSON.parse(readFileSync(policyPath, "utf8"));
    const priorSha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");
    if (priorPolicy.version !== 1
      || priorSha256(output) !== priorPolicy.wrapperSha256
      || priorSha256(safeConfig) !== priorPolicy.configSha256) {
      fail("refusing to overwrite browser wrapper artifacts that do not match their generator policy");
    }
  } catch (error) {
    if (error instanceof SyntaxError) fail("refusing to overwrite browser wrapper artifacts with an invalid policy");
    throw error;
  }
}
const blockedFlags = ["--allowed-domains", "--config"];
const wrapperText = `#!/usr/bin/env node
import { spawnSync } from "node:child_process";
const browserExecutable = ${JSON.stringify(browserExecutable)};
const safeConfig = ${JSON.stringify(safeConfig)};
const allowedDomains = ${JSON.stringify(args.allowedDomains.join(","))};
const blockedFlags = ${JSON.stringify(blockedFlags)};
const callerArgs = process.argv.slice(2);
const optionName = (value) => value.includes("=") ? value.slice(0, value.indexOf("=")) : value;
if (callerArgs[0] === "connect" || callerArgs.some((value) => blockedFlags.includes(optionName(value)))) {
  process.stderr.write("Scoped browser wrapper: caller must not override --allowed-domains or the generated configuration.\\n");
  process.exit(64);
}
const environment = { ...process.env, AGENT_BROWSER_ALLOWED_DOMAINS: allowedDomains };
const result = spawnSync(browserExecutable, ["--config", safeConfig, "--allowed-domains", allowedDomains, ...callerArgs], {
  env: environment,
  stdio: "inherit",
  shell: false,
});
if (result.error) {
  process.stderr.write("Scoped browser wrapper: browser executable could not be started.\\n");
  process.exit(1);
}
if (result.signal) {
  process.kill(process.pid, result.signal);
} else {
  process.exit(result.status ?? 1);
}
`;
const sha256 = (text) => createHash("sha256").update(text).digest("hex");
const policy = {
  version: 1,
  browserExecutable,
  allowedDomains: args.allowedDomains,
  wrapperSha256: sha256(wrapperText),
  configPath: safeConfig,
  configSha256: sha256(safeConfigText),
};

for (const [path, contents, mode] of [
  [safeConfig, safeConfigText, 0o600],
  [output, wrapperText, 0o755],
  [policyPath, `${JSON.stringify(policy, null, 2)}\n`, 0o600],
]) {
  atomicWrite(path, contents, mode);
}

process.stdout.write(`BROWSER_WRAPPER=${relative(projectRoot, output)}\nBROWSER_ALLOWED_DOMAINS=${args.allowedDomains.join(",")}\n`);
