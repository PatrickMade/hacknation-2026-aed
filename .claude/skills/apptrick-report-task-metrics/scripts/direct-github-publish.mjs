#!/usr/bin/env node
// Explicitly approved direct transport only; credentials stay in this process.
import { constants, closeSync, fstatSync, lstatSync, openSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { request as httpsRequest, Agent } from 'node:https';
import { checkServerIdentity } from 'node:tls';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { retain, publicationHTTPDiagnostics, publicationValidationDiagnostics, publicationCredentialDiagnostics } from './local-report.mjs';
import { validatePublicationPayload } from './validate-payload.mjs';

function privateJSON(path) {
  const info = lstatSync(path);
  if (!info.isFile() || info.isSymbolicLink() || info.uid !== process.getuid() || info.nlink !== 1 || (info.mode & 0o777) !== 0o600) throw new Error('private_artifact_unavailable');
  const fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const info = fstatSync(fd);
    if (!info.isFile() || info.uid !== process.getuid() || info.nlink !== 1 || (info.mode & 0o777) !== 0o600 || info.size > 2 * 1024 * 1024) throw new Error('private_artifact_unavailable');
    return JSON.parse(readFileSync(fd, 'utf8'));
  } finally { closeSync(fd); }
}
const initialDiagnostics = process.env.NODE_DEBUG ?? '';
function safeTransportEnvironment() {
  if (initialDiagnostics || process.env.NODE_DEBUG || process.env.NODE_DEBUG_NATIVE || process.env.NODE_TLS_REJECT_UNAUTHORIZED === '0') throw new Error('tools_unavailable');
}
function credential(project) {
  const env = { ...process.env };
  for (const k of ['GH_DEBUG', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NODE_USE_ENV_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'node_use_env_proxy']) delete env[k];
  const account = spawnSync('git', ['-C', project, 'config', '--get', 'github.requiredaccount'], { encoding: 'utf8', env, timeout: 5000, maxBuffer: 4096 });
  const args = ['auth', 'token', '--hostname', 'github.com'];
  if (account.status === 0) {
    const required = account.stdout.trim();
    if (!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/.test(required)) throw new Error('access_unavailable');
    args.push('--user', required);
    // A required account must never be replaced by an environment credential.
    for (const key of ['GH_TOKEN', 'GITHUB_TOKEN', 'GH_ENTERPRISE_TOKEN', 'GITHUB_ENTERPRISE_TOKEN']) delete env[key];
  } else if (account.status !== 1) throw new Error('access_unavailable');
  // Account guards may verify the selected login before returning its token.
  const result = spawnSync('gh', args, { encoding: 'utf8', env, timeout: 15000, maxBuffer: 8192 });
  if (result.error?.code === 'ETIMEDOUT') {
    throw Object.assign(new Error('access_unavailable'), { credential_error: 'credential_timeout' });
  }
  const token = result.status === 0 ? result.stdout.trim() : '';
  if (!/^[A-Za-z0-9_]{20,4096}$/.test(token)) throw new Error('access_unavailable');
  return token;
}
export function directHTTPSRequest(endpoint, path, payload, token, transport = httpsRequest) {
  safeTransportEnvironment();
  if (!['/receipts', '/reports'].includes(path)) throw new Error('invalid_operation');
  const body = JSON.stringify(payload);
  return new Promise((resolvePromise, reject) => {
    const agent = new Agent({ rejectUnauthorized: true, checkServerIdentity }); // no environment proxy/global agent
    const req = transport(endpoint + path, { method: 'POST', agent, rejectUnauthorized: true, checkServerIdentity, headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token, 'Content-Length': Buffer.byteLength(body) } }, response => {
      const chunks = []; let bytes = 0;
      response.on('data', chunk => {
        bytes += chunk.length;
        if (bytes > 8192) {
          // Abort bounded buffering without losing the already-observed status.
          resolvePromise({ status: response.statusCode, value: null });
          agent.destroy(); req.destroy();
        } else chunks.push(chunk);
      });
      response.on('error', reject);
      response.on('end', () => {
        let value = null;
        try { value = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { /* Keep status only; never retain malformed response text. */ }
        resolvePromise({ status: response.statusCode, value });
        agent.destroy();
      });
    });
    req.setTimeout(10000, () => req.destroy(new Error('offline')));
    req.on('error', error => { agent.destroy(); reject(error); });
    req.end(body);
  });
}
export async function publishDirect(options, dependencies = {}) {
  const args = ['--project', options.project, '--run-id', options.runId, '--task-ref', options.taskRef];
  if (options.inspect) return { status: 'not_written' };
  const read = retain([...args, '--operation', 'read'], JSON.stringify({ revision: options.revision }));
  if (read.status !== 'pending' || options.local) return read;
  let source = read.artifact_path, cause = 'tools_unavailable', diagnostics = {};
  const update = (operation, data) => retain([...args, '--operation', operation], JSON.stringify({ revision: options.revision, ...data }));
  try {
    const bundle = privateJSON(source);
    const descriptor = privateJSON(options.transport);
    if (!/^[A-Za-z0-9_-]{1,128}$/.test(options.sourceId ?? '') || !/^[A-Za-z0-9_-]{1,128}$/.test(options.validationSourceId ?? '')) throw new Error('missing_binding');
    validatePublicationPayload(bundle.payload);
    if (descriptor.kind !== 'direct_github' || descriptor.credential_forwarding_approved !== true || descriptor.enabled !== true || !/^https:\/\/[a-z0-9]{10}\.execute-api\.[a-z]{2}-[a-z]+-[0-9]\.amazonaws\.com\/[A-Za-z0-9_-]{1,64}$/.test(descriptor.endpoint)
        || descriptor.project_id !== bundle.payload?.project_id || descriptor.destination_id !== bundle.destination_id) throw new Error('missing_binding');
    const identity = Object.fromEntries(['project_id', 'task_id', 'report_key', 'revision'].map(k => [k, bundle.payload[k]]));
    safeTransportEnvironment();
    const token = (dependencies.credential ?? credential)(options.project); // never print/pass via argv/files
    const request = dependencies.send ?? directHTTPSRequest;
    const receipt = value => {
      if (!value || value.status !== 'stored' || Object.entries(identity).some(([k, v]) => value[k] !== v) || value.payload_sha256 !== bundle.canonical_sha256) throw new Error('conflicting_receipt');
      return update('receipt', { source_id: options.sourceId, receipt: { ...identity, destination_id: descriptor.destination_id, canonicalSHA256: value.payload_sha256 } });
    };
    const found = await request(descriptor.endpoint, '/receipts', identity, token);
    if (found.status === 200) return receipt(found.value);
    diagnostics = publicationHTTPDiagnostics('receipts', found.status, found.value?.error);
    if (found.status !== 404 || found.value?.error !== 'receipt_not_found') throw new Error(found.status === 403 ? 'access_unavailable' : 'readback_unavailable');
    diagnostics = {};
    if (bundle.publication.submit_attempts > 0) throw new Error('submission_failed');
    const lookup = { ...identity, destination_id: descriptor.destination_id, canonicalSHA256: bundle.canonical_sha256 };
    update('not-found', { source_id: options.sourceId, lookup, after_submit_attempt: bundle.publication.submit_attempts });
    update('attempt', { validation_source_id: options.validationSourceId });
    cause = 'uncertain_write';
    let submitted;
    try { submitted = await request(descriptor.endpoint, '/reports', bundle.payload, token); } catch { submitted = null; }
    if (submitted && submitted.status !== 200) diagnostics = publicationHTTPDiagnostics('reports', submitted.status, submitted.value?.error);
    if (submitted?.status === 200) receiptCheck(submitted.value, identity, bundle.canonical_sha256);
    else if (submitted && ![500,502,503,504].includes(submitted.status)) throw new Error(submitted.status === 409 ? 'conflicting_receipt' : submitted.status === 403 ? 'access_unavailable' : 'submission_failed');
    if (submitted && submitted.status !== 200) update('pending', { reason: cause, ...diagnostics });
    const final = await request(descriptor.endpoint, '/receipts', identity, token);
    if (final.status === 200) return receipt(final.value);
    diagnostics = publicationHTTPDiagnostics('receipts', final.status, final.value?.error);
    throw new Error('readback_unavailable');
  } catch (error) {
    if (error?.message === 'access_unavailable') {
      diagnostics = { ...diagnostics, ...publicationCredentialDiagnostics(error.credential_error) };
    }
    if (error?.message === 'invalid_publication_payload') {
      cause = 'invalid_payload';
      // Only shared fixed chronology/actor code-path pairs may be retained.
      diagnostics = publicationValidationDiagnostics(error.validation_error, error.validation_path);
    }
    const allowed = ['missing_binding', 'access_unavailable', 'offline', 'readback_unavailable', 'conflicting_receipt', 'submission_failed', 'report_too_large'];
    cause = allowed.includes(error?.message) ? error.message : cause;
    try { return update('pending', { reason: cause, ...diagnostics }); }
    catch { return { status: 'pending', artifact_path: source, reason: 'private_storage_unavailable' }; }
  }
}
function receiptCheck(value, identity, digest) {
  if (!value || value.status !== 'stored' || Object.entries(identity).some(([k, v]) => value[k] !== v) || value.payload_sha256 !== digest) throw new Error('conflicting_receipt');
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const options = {};
    const names = { '--project': 'project', '--run-id': 'runId', '--task-ref': 'taskRef', '--revision': 'revision', '--transport': 'transport', '--source-id': 'sourceId', '--validation-source-id': 'validationSourceId' };
    const args = process.argv.slice(2);
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--inspect' || args[i] === '--local') { options[args[i].slice(2)] = true; continue; }
      const name = names[args[i]];
      if (!name || options[name] !== undefined || !args[i + 1] || args[i + 1].startsWith('--')) throw new Error();
      options[name] = args[++i];
    }
    options.revision = Number(options.revision);
    console.log(JSON.stringify(await publishDirect(options)));
  } catch { console.error('Direct metrics publication unavailable. Preserve the local report; task delivery is unchanged.'); process.exitCode = 2; }
}
