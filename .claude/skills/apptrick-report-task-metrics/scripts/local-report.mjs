#!/usr/bin/env node
// Private local retention only. Native tools own schema validation and transport.
import { execFileSync } from 'node:child_process';
import { constants, closeSync, existsSync, fstatSync, fsyncSync, lstatSync, mkdirSync, openSync, readFileSync, realpathSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
const fail = () => { throw new Error('invalid report, identity, state or private storage'); };
const id = v => typeof v === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(v);
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const canonical = v => JSON.stringify(sort(v));
function sort(v) {
  if (Array.isArray(v)) return v.map(sort);
  if (!object(v)) return v;
  return Object.fromEntries(Object.keys(v).sort().map(k => [k, sort(v[k])]));
}
const hash = v => createHash('sha256').update(canonical(v), 'utf8').digest('hex');
const reasons = ['awaiting_submission', 'missing_binding', 'access_unavailable', 'tools_unavailable', 'offline', 'submission_failed', 'readback_unavailable', 'uncertain_write', 'conflicting_receipt', 'invalid_payload', 'report_too_large'];
const httpErrors = new Set(['report_too_large', 'invalid_request', 'access_denied', 'revision_conflict', 'receipt_not_found', 'operation_unavailable']);
export function publicationHTTPDiagnostics(operation, status, code) {
  if (!['reports', 'receipts'].includes(operation) || !Number.isInteger(status) || status < 100 || status > 599) return {};
  return { http_operation: operation, http_status: status, ...(httpErrors.has(code) ? { error_code: code } : {}) };
}
export function publicationValidationDiagnostics(code, path) {
  if (typeof path !== 'string') return {};
  const chronology = code === 'end_before_start'
    && /^(?:attempts|intervals|rounds|usage\.requests|cost\.applied_rates)\[(?:0|[1-9][0-9]{0,3})\]\.end$(?![\s\S])/.test(path);
  const actor = code === 'unknown_actor'
    && /^intervals\[(?:0|[1-9][0-9]{0,3})\]\.actor_id$(?![\s\S])/.test(path);
  if (!chronology && !actor) return {};
  return { validation_error: code, validation_path: path };
}
export function publicationCredentialDiagnostics(code) {
  return code === 'credential_timeout' ? { credential_error: code } : {};
}
const metricKeys = ['calendar_ms', 'delivery_ms', 'actor_activity_ms', 'technical_wait_ms', 'human_block_ms', 'suspension_ms'];
function metrics(v) {
  if (!object(v) || Object.entries(v).some(([k, n]) => !metricKeys.includes(k) || n !== null && (!Number.isFinite(n) || n < 0))) fail();
}
function checkStat(s, directory) {
  if (s.isSymbolicLink() || s.uid !== process.getuid() || (s.mode & 0o777) !== (directory ? 0o700 : 0o600) || !(directory ? s.isDirectory() : s.isFile() && s.nlink === 1)) fail();
}
function privatePath(path, directory = false) { checkStat(lstatSync(path), directory); }
function privateDir(path) {
  try { mkdirSync(path, { mode: 0o700 }); } catch (e) { if (e.code !== 'EEXIST') throw e; }
  privatePath(path, true);
}
function readPrivate(path) {
  privatePath(path);
  const fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try { checkStat(fstatSync(fd), false); return JSON.parse(readFileSync(fd, 'utf8')); } finally { closeSync(fd); }
}
function atomic(path, value) {
  if (existsSync(path)) privatePath(path);
  const temp = join(dirname(path), `.report-${randomUUID()}.tmp`);
  const fd = openSync(temp, 'wx', 0o600);
  try {
    try { writeFileSync(fd, JSON.stringify(value, null, 2) + '\n'); fsyncSync(fd); } finally { closeSync(fd); }
    renameSync(temp, path);
    const directory = openSync(dirname(path), constants.O_RDONLY);
    try { fsyncSync(directory); } finally { closeSync(directory); }
  } finally { if (existsSync(temp)) unlinkSync(temp); }
}
const identityKeys = ['project_id', 'task_id', 'report_key', 'revision'];
function checkPayload(payload, runId, revision) {
  if (!object(payload) || payload.schema_version !== 1 || !identityKeys.slice(0, 3).every(k => id(payload[k])) || payload.revision !== revision || !Array.isArray(payload.run_ids) || !payload.run_ids.includes(runId) || !payload.run_ids.every(id)) fail();
  const fields = ['schema_version', ...identityKeys, 'run_ids', 'boundary', 'outcome', 'classification', 'coverage', 'attempts', 'intervals', 'rounds', 'usage', 'metrics', 'cost', 'estimation_ref', 'reporting_overhead'];
  if (Object.keys(payload).some(k => !fields.includes(k)) || !['partial_checkpoint', 'verified_delivery'].includes(payload.boundary) || !['completed', 'blocked', 'aborted', 'partial', 'no_action'].includes(payload.outcome)) fail();
  metrics(payload.metrics);
  // Full nested allowlist/schema validation is required through the native service.
}
export function retain(args, raw) {
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    const k = args[i];
    if (['--inspect', '--local'].includes(k)) { if (opts[k]) fail(); opts[k] = true; continue; }
    if (!['--project', '--run-id', '--task-ref', '--operation'].includes(k) || opts[k] !== undefined || !args[i + 1] || args[i + 1].startsWith('--')) fail();
    opts[k] = args[++i];
  }
  const runId = opts['--run-id'], taskRef = opts['--task-ref'], op = opts['--operation'];
  if (!opts['--project'] || !id(runId) || typeof taskRef !== 'string' || !taskRef || taskRef.length > 1024 || !['prepare', 'read', 'attempt', 'pending', 'not-found', 'receipt'].includes(op)) fail();
  if (opts['--inspect']) return { status: 'not_written' };
  if (typeof process.getuid !== 'function') fail();
  const root = realpathSync(resolve(opts['--project']));
  const config = JSON.parse(readFileSync(join(root, '.ai/agentic.config.json'), 'utf8'));
  if (config.metrics?.enabled !== undefined && typeof config.metrics.enabled !== 'boolean') fail();
  if (config.metrics?.enabled !== true) return { status: 'disabled' };
  if (Buffer.byteLength(raw) > 2 * 1024 * 1024) fail();
  const input = JSON.parse(raw);
  if (!object(input) || !Number.isSafeInteger(input.revision) || input.revision < 1) fail();
  if (opts['--local'] && op !== 'prepare' && op !== 'read') fail();
  if (op === 'prepare') {
    if (!object(input.report) || input.report.schema_version !== 1 || input.report.run_id !== runId || input.report.task_ref !== taskRef || !reasons.includes(input.reason)) fail();
    metrics(input.report.metrics);
    if (input.payload !== null) checkPayload(input.payload, runId, input.revision);
    if (input.payload === null ? input.destination_id !== null : !id(input.destination_id)) fail();
  }
  const common = realpathSync(resolve(root, execFileSync('git', ['-C', root, 'rev-parse', '--git-common-dir'], { encoding: 'utf8' }).trim()));
  const storage = join(common, 'task-metrics');
  const run = join(storage, runId);
  if (op === 'read') { privatePath(storage, true); privatePath(run, true); }
  else { privateDir(storage); privateDir(run); }
  const lifecycle = join(run, 'lifecycle.json');
  if (existsSync(lifecycle)) {
    const captured = readPrivate(lifecycle);
    if (captured.run_id !== runId || captured.task_ref !== taskRef) fail();
  }
  const lock = join(run, 'report.lock');
  const fd = op === 'read' ? null : openSync(lock, 'wx', 0o600);
  try {
    if (fd !== null) { writeFileSync(fd, JSON.stringify({ owner_pid: process.pid, created_at: new Date().toISOString() }) + '\n'); fsyncSync(fd); }
    const contextPath = join(run, 'report-context.json');
    const context = existsSync(contextPath) ? readPrivate(contextPath) : null;
    if (context && (context.schema_version !== 1 || context.run_id !== runId || context.task_ref !== taskRef)) fail();
    if (!context && op !== 'prepare') fail();
    if (!context) atomic(contextPath, { schema_version: 1, run_id: runId, task_ref: taskRef });
    const path = join(run, `report-${input.revision}.json`);
    let bundle = existsSync(path) ? readPrivate(path) : null;
    if (bundle && (bundle.schema_version !== 1 || bundle.run_id !== runId || bundle.task_ref !== taskRef || bundle.revision !== input.revision || bundle.report_sha256 !== hash(bundle.report) || bundle.canonical_sha256 !== (bundle.payload === null ? null : hash(bundle.payload)))) fail();
    if (op === 'prepare') {
      const reportHash = hash(input.report), payloadHash = input.payload === null ? null : hash(input.payload);
      if (bundle) {
        if (bundle.report_sha256 !== reportHash || bundle.canonical_sha256 !== payloadHash || bundle.destination_id !== input.destination_id || opts['--local'] && bundle.publication.status !== 'local_only') fail();
      } else {
        bundle = { schema_version: 1, run_id: runId, task_ref: taskRef, revision: input.revision, report: sort(input.report), payload: input.payload === null ? null : sort(input.payload), report_sha256: reportHash, canonical_sha256: payloadHash, destination_id: input.destination_id, transport_validation: 'required', publication: { status: opts['--local'] ? 'local_only' : 'pending', reason: input.reason, submit_attempts: 0, may_have_been_submitted: false, receipt: null, observations: [] } };
        atomic(path, bundle);
      }
    } else {
      if (!bundle) fail();
      const pub = bundle.publication;
      if (op !== 'read') {
        if (pub.status !== 'pending') fail();
        const now = new Date().toISOString();
        if (op === 'pending') {
          if (!reasons.includes(input.reason)) fail();
          if (['http_operation', 'http_status', 'error_code'].some(k => Object.hasOwn(input, k))) {
            const diagnostic = publicationHTTPDiagnostics(input.http_operation, input.http_status, input.error_code);
            if (!diagnostic.http_status || Object.hasOwn(input, 'error_code') && diagnostic.error_code !== input.error_code) fail();
          }
          if (['validation_error', 'validation_path'].some(k => Object.hasOwn(input, k))) {
            if (input.reason !== 'invalid_payload' || !publicationValidationDiagnostics(input.validation_error, input.validation_path).validation_path) fail();
          }
          if (Object.hasOwn(input, 'credential_error') && (input.reason !== 'access_unavailable'
              || !publicationCredentialDiagnostics(input.credential_error).credential_error)) fail();
          pub.reason = input.reason;
        } else {
          if (bundle.payload === null) fail();
          if (op === 'attempt') {
            if (pub.may_have_been_submitted || !id(input.validation_source_id)) fail();
            pub.may_have_been_submitted = true; pub.submit_attempts++; pub.reason = 'uncertain_write';
          } else if (op === 'not-found') {
            const lookup = input.lookup;
            if (!id(input.source_id) || pub.observations.some(o => o.source_id === input.source_id) || input.after_submit_attempt !== pub.submit_attempts || !object(lookup) || !identityKeys.every(k => lookup[k] === bundle.payload[k]) || lookup.destination_id !== bundle.destination_id || lookup.canonicalSHA256 !== bundle.canonical_sha256) fail();
            pub.may_have_been_submitted = false; pub.reason = 'awaiting_submission';
          } else if (op === 'receipt') {
            const receipt = input.receipt;
            if (!object(receipt) || Object.keys(receipt).some(k => ![...identityKeys, 'destination_id', 'canonicalSHA256'].includes(k)) || !identityKeys.every(k => receipt[k] === bundle.payload[k]) || receipt.destination_id !== bundle.destination_id || receipt.canonicalSHA256 !== bundle.canonical_sha256 || !id(input.source_id)) fail();
            pub.status = 'stored'; pub.reason = null; pub.receipt = receipt;
          }
        }
        pub.observations.push({ operation: op, at: now, reason: pub.reason, source_id: input.source_id ?? input.validation_source_id ?? null,
          ...(op === 'pending' ? { ...publicationHTTPDiagnostics(input.http_operation, input.http_status, input.error_code),
            ...publicationValidationDiagnostics(input.validation_error, input.validation_path),
            ...publicationCredentialDiagnostics(input.credential_error) } : {}) });
        pub.observations = pub.observations.slice(-16);
        atomic(path, bundle);
      }
    }
    const pub = bundle.publication;
    return { status: pub.status, artifact_path: path, canonical_sha256: bundle.canonical_sha256, next_action: pub.status !== 'pending' ? 'none' : bundle.payload === null ? 'bind_transport' : pub.may_have_been_submitted ? 'reconcile_receipt' : 'validate_and_submit' };
  } finally { if (fd !== null) { closeSync(fd); unlinkSync(lock); } }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { console.log(JSON.stringify(retain(process.argv.slice(2), readFileSync(0, 'utf8')))); }
  catch { console.error('Local metrics report failed: invalid input, conflicting identity/state, or unavailable private storage. Preserve existing artifacts; delivery status is unchanged.'); process.exitCode = 2; }
}
