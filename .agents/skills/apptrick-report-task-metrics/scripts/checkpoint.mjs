#!/usr/bin/env node
// Local observation capture only: no transport, authentication or usage inference.
import { execFileSync } from 'node:child_process';
import { constants, closeSync, existsSync, fsyncSync, lstatSync, mkdirSync, openSync, readFileSync, realpathSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

const fail = () => { throw new Error('invalid checkpoint or private storage; preserve evidence and report a metrics gap'); };
const id = x => typeof x === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(x);
const phases = ['intake', 'diagnosis', 'specification', 'planning', 'implementation', 'correction', 'validation', 'review', 'browser', 'qa', 'e2e', 'finalisation'];
const states = ['active', 'technical_wait', 'human_block', 'suspended', 'unknown'];
const types = ['begin', 'checkpoint', 'resume', 'handoff', 'close'];
function privatePath(path, directory) {
  const s = lstatSync(path);
  if (s.isSymbolicLink() || s.uid !== process.getuid() || (s.mode & 0o777) !== (directory ? 0o700 : 0o600) || !(directory ? s.isDirectory() : s.isFile() && s.nlink === 1)) fail();
}
function privateDir(path) {
  if (!existsSync(path)) mkdirSync(path, { mode: 0o700 });
  privatePath(path, true);
}
function readPrivate(path) {
  privatePath(path, false);
  const fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try { return JSON.parse(readFileSync(fd, 'utf8')); } finally { closeSync(fd); }
}
function atomic(path, data) {
  if (existsSync(path)) privatePath(path, false);
  const temp = join(dirname(path), `.checkpoint-${randomUUID()}.tmp`);
  const fd = openSync(temp, 'wx', 0o600);
  try { writeFileSync(fd, JSON.stringify(data, null, 2) + '\n'); fsyncSync(fd); }
  finally { closeSync(fd); }
  try { renameSync(temp, path); } finally { if (existsSync(temp)) unlinkSync(temp); }
}
export function capture(args, input) {
  const options = {};
  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    if (key === '--inspect') { if (options.inspect) fail(); options.inspect = true; continue; }
    if (!['--project', '--run-id', '--task-ref'].includes(key) || options[key] !== undefined || !args[i + 1] || args[i + 1].startsWith('--')) fail();
    options[key] = args[++i];
  }
  if (!options['--project'] || !id(options['--run-id']) || typeof options['--task-ref'] !== 'string' || !options['--task-ref'] || options['--task-ref'].length > 1024) fail();
  if (options.inspect) return { status: 'not_written' };
  if (typeof process.getuid !== 'function') fail();
  const root = realpathSync(resolve(options['--project']));
  const config = JSON.parse(readFileSync(join(root, '.ai/agentic.config.json'), 'utf8'));
  if (config.metrics?.enabled !== undefined && typeof config.metrics.enabled !== 'boolean') fail();
  if (config.metrics?.enabled !== true) return { status: 'disabled' };
  if (Buffer.byteLength(input) > 16384) fail();
  const event = JSON.parse(input);
  if (!event || typeof event !== 'object' || Array.isArray(event) || Object.keys(event).some(k => !['event_id', 'type', 'actor_id', 'attempt_id', 'phase', 'state', 'outcome', 'boundary'].includes(k))) fail();
  if (!id(event.event_id) || !id(event.actor_id) || !id(event.attempt_id) || !types.includes(event.type) || !phases.includes(event.phase) || !states.includes(event.state)) fail();
  if (event.type === 'close') {
    if (!['completed', 'blocked', 'aborted', 'partial', 'no_action'].includes(event.outcome) || !['partial_checkpoint', 'verified_delivery'].includes(event.boundary)) fail();
  } else if (event.outcome !== undefined || event.boundary !== undefined) fail();
  // Git metadata is shared by this clone's linked worktrees; capture survives cleanup.
  const common = realpathSync(resolve(root, execFileSync('git', ['-C', root, 'rev-parse', '--git-common-dir'], { encoding: 'utf8' }).trim()));
  const storage = join(common, 'task-metrics');
  privateDir(storage);
  const run = join(storage, options['--run-id']);
  privateDir(run);
  const lock = join(run, 'checkpoint.lock');
  const fd = openSync(lock, 'wx', 0o600);
  try {
    const path = join(run, 'lifecycle.json');
    const ledger = existsSync(path) ? readPrivate(path) : {
      schema_version: 1, run_id: options['--run-id'], task_ref: options['--task-ref'],
      start_scope: 'bound_run', events: [],
      metrics: { calendar_ms: null, delivery_ms: null, actor_activity_ms: null, technical_wait_ms: null, human_block_ms: null, suspension_ms: null },
      clock: { basis: 'wall_clock', alignment: 'unverified' },
    };
    if (ledger.schema_version !== 1 || ledger.run_id !== options['--run-id'] || ledger.task_ref !== options['--task-ref'] || !Array.isArray(ledger.events)) fail();
    const duplicate = ledger.events.find(e => e.input.event_id === event.event_id);
    if (duplicate) {
      if (JSON.stringify(Object.fromEntries(Object.entries(duplicate.input).sort())) !== JSON.stringify(Object.fromEntries(Object.entries(event).sort()))) fail();
      return { status: 'unchanged', ledger_path: path, event_count: ledger.events.length };
    }
    const previous = ledger.events.at(-1);
    if (event.type === 'begin' && previous) fail();
    if (!previous && !['begin', 'resume'].includes(event.type)) fail();
    if (previous && ['close', 'handoff'].includes(previous.input.type) && event.type !== 'resume') fail();
    const now = new Date().toISOString();
    // Never turn an unobserved interval between invocations into active time.
    const gap = event.type === 'resume' || !previous && event.type !== 'begin';
    const clockRegression = Boolean(previous && now < previous.recorded_at);
    ledger.events.push({ input: event, recorded_at: now, gap_before: gap, clock_regression: clockRegression });
    atomic(path, ledger);
    return { status: 'recorded', ledger_path: path, event_count: ledger.events.length };
  } finally { closeSync(fd); unlinkSync(lock); }
}

if (process.argv[1] && resolve(process.argv[1]) === realpathSync(new URL(import.meta.url))) {
  try { console.log(JSON.stringify(capture(process.argv.slice(2), readFileSync(0, 'utf8')))); }
  catch { console.error('Metrics checkpoint failed: invalid input, conflicting identity/event, or unavailable private storage. Delivery status is unchanged.'); process.exitCode = 2; }
}
