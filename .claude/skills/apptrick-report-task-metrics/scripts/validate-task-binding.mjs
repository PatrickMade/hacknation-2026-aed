#!/usr/bin/env node
// Caller supplies approved config and authenticated tracker metadata, never parsed author claims.
import { readFileSync } from 'node:fs';
const invalid = () => { throw new Error('unverified task binding'); };
const textId = x => typeof x === 'string' && x.length > 0 && x.length <= 1024;
const fields = (x, keys) => x && typeof x === 'object' && !Array.isArray(x) && Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x, k));
export function validateTaskBinding(input) {
  if (!fields(input, ['approved', 'binding', 'comment'])) invalid();
  const { approved: a, binding: b, comment: c } = input;
  if (!fields(a, ['project_id', 'repository_id', 'task_native_id', 'author_ids']) || !fields(b, ['project_id', 'task_id', 'repository_id', 'task_native_id']) || !fields(c, ['author_id', 'repository_id', 'task_native_id'])) invalid();
  if (!/^prj_[0-9a-f]{32}$/.test(a.project_id) || !/^tsk_[0-9a-f]{32}$/.test(b.task_id)) invalid();
  if (![a.repository_id, a.task_native_id, c.author_id].every(textId) || !Array.isArray(a.author_ids) || !a.author_ids.length || a.author_ids.length > 1000 || !a.author_ids.every(textId)) invalid();
  if (!a.author_ids.includes(c.author_id) || b.project_id !== a.project_id || b.repository_id !== a.repository_id || c.repository_id !== a.repository_id || b.task_native_id !== a.task_native_id || c.task_native_id !== a.task_native_id) invalid();
  return { project_id: b.project_id, task_id: b.task_id };
}
try {
  const input = readFileSync(0, 'utf8');
  if (Buffer.byteLength(input) > 65536) invalid();
  console.log(JSON.stringify(validateTaskBinding(JSON.parse(input))));
} catch {
  console.error('Metrics task binding is unverified; retain publication pending.');
  process.exitCode = 2;
}
