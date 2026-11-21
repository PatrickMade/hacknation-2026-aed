#!/usr/bin/env node

const args = process.argv.slice(2);
const value = (name) => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : undefined;
};

const provider = value("--provider");
const reference = value("--reference");
const input = value("--input");
const configuredHost = value("--host")?.toLowerCase();
const configuredProject = value("--project")?.toUpperCase();
const configuredRepository = value("--repository")?.toLowerCase();
const configuredWorkspace = value("--workspace")?.toLowerCase();

const fail = () => {
  process.stderr.write(`Invalid issue reference for ${provider ?? "unknown provider"}.\n`);
  process.exit(2);
};

if (!provider || (Boolean(reference) === Boolean(input)) || args.length < 4 || args.length > 10 || args.length % 2 !== 0) fail();
if (!["github", "jira", "linear"].includes(provider)) fail();

const classifyMode = input !== undefined;
const rawInput = reference ?? input;
const issueShaped = /^(?:#?[0-9]+|[A-Za-z][A-Za-z0-9_]{0,31}-[0-9]+|https?:\/\/\S+)$/.test(rawInput);
if (classifyMode && !issueShaped) {
  process.stdout.write(`${JSON.stringify({ kind: "brief", brief: rawInput })}\n`);
  process.exit(0);
}

let parsedReference;
try {
  parsedReference = rawInput.startsWith("https://") ? new URL(rawInput) : undefined;
} catch {
  parsedReference = undefined;
}
const issueFromUrl = (pattern) => {
  if (parsedReference?.protocol !== "https:" || parsedReference.username || parsedReference.password || parsedReference.port || !configuredHost || parsedReference.hostname.toLowerCase() !== configuredHost) return undefined;
  return parsedReference.pathname.match(pattern)?.[1];
};

let issueId;
if (provider === "github") {
  const short = rawInput.match(/^#?([1-9][0-9]*)$/);
  const match = parsedReference?.protocol === "https:" && !parsedReference.username && !parsedReference.password && !parsedReference.port && parsedReference.hostname.toLowerCase() === configuredHost
    ? parsedReference.pathname.match(/^\/([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\/issues\/([1-9][0-9]*)\/?$/)
    : undefined;
  issueId = short?.[1] ?? (configuredRepository && match?.[1].toLowerCase() === configuredRepository ? match[2] : undefined);
} else {
  const direct = /^[A-Z][A-Z0-9_]{1,31}-[1-9][0-9]*$/.test(rawInput) ? rawInput : undefined;
  let fromUrl = provider === "jira"
    ? issueFromUrl(/^\/browse\/([A-Z][A-Z0-9_]{1,31}-[1-9][0-9]*)\/?$/)
    : issueFromUrl(/^\/[^/]+\/issue\/([A-Z][A-Z0-9_]{1,31}-[1-9][0-9]*)(?:\/[^/]*)?\/?$/);
  if (provider === "linear" && fromUrl) {
    const workspace = parsedReference.pathname.split("/")[1]?.toLowerCase();
    if (!configuredWorkspace || workspace !== configuredWorkspace) fromUrl = undefined;
  }
  issueId = direct ?? fromUrl;
  if (issueId && configuredProject && !issueId.startsWith(`${configuredProject}-`)) issueId = undefined;
}

if (!issueId) fail();

process.stdout.write(`${JSON.stringify({
  ...(classifyMode ? { kind: "issue" } : {}),
  provider,
  issueId,
  markerId: provider === "github" ? `#${issueId}` : issueId,
  ...(rawInput.startsWith("https://") ? { sourceUrl: rawInput } : {}),
})}\n`);
