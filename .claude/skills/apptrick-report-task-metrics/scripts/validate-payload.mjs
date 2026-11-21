// Closed structural/privacy and bounded local consistency checks. The remote
// service owns remaining semantic/source validation. Unknown keywords fail closed.
import { readFileSync } from 'node:fs';
const schema = JSON.parse(readFileSync(new URL('../references/report.schema.json', import.meta.url), 'utf8'));
const fail = () => { throw new Error('invalid_publication_payload'); };
// Structural validation has already limited timestamps to UTC and 0-6 fractional
// digits. Pad to equal precision: Date.parse would lose sub-millisecond order.
const instant = value => value.slice(0, 19) + '.' + value.slice(19, -1).replace(/^\./, '').padEnd(6, '0');
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const supported = new Set(['$schema', '$id', '$defs', 'type', 'enum', 'anyOf', 'pattern', 'minimum', 'maximum', 'properties', 'required', 'additionalProperties', 'items', 'maxItems', 'uniqueItems', 'minItems', 'maxLength', 'format']);
function check(value, rule) {
  if (Object.keys(rule).some(k => !supported.has(k))) fail();
  if (rule.anyOf) {
    if (!rule.anyOf.some(candidate => { try { check(value, candidate); return true; } catch { return false; } })) fail();
    return;
  }
  if (rule.enum && !rule.enum.some(v => v === value)) fail();
  if (rule.type) {
    const actual = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
    if (rule.type === 'integer' ? !Number.isSafeInteger(value) : actual !== rule.type) fail();
  }
  if (typeof value === 'number' && (!Number.isFinite(value) || rule.minimum !== undefined && value < rule.minimum || rule.maximum !== undefined && value > rule.maximum)) fail();
  if (typeof value === 'string') {
    if (rule.pattern && !new RegExp(rule.pattern).test(value) || rule.maxLength !== undefined && Array.from(value).length > rule.maxLength) fail();
    if (rule.format) {
      if (rule.format !== 'date-time' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0,19) !== value.slice(0,19)) fail();
    }
  }
  if (Array.isArray(value)) {
    if (rule.minItems !== undefined && value.length < rule.minItems || rule.maxItems !== undefined && value.length > rule.maxItems) fail();
    if (rule.uniqueItems && new Set(value.map(v => JSON.stringify(v))).size !== value.length) fail();
    for (const v of value) check(v, rule.items ?? {});
  }
  if (plain(value)) {
    if (rule.required?.some(k => !Object.hasOwn(value, k))) fail();
    for (const [k,v] of Object.entries(value)) {
      if (!Object.hasOwn(rule.properties ?? {},k)) { if (rule.additionalProperties === false) fail(); }
      else check(v,rule.properties[k]);
    }
  }
}
export function validatePublicationPayload(payload) {
  if (Buffer.byteLength(JSON.stringify(payload),'utf8') + 16384 > 256 * 1024) throw new Error('report_too_large');
  check(payload,schema);
  const coverage = payload.coverage;
  const declared = new Set(coverage.source_ids), missing = new Set(coverage.missing_source_ids);
  if (coverage.covered_sources !== declared.size || [...missing].some(source => declared.has(source))) fail();
  if (coverage.missing_sources !== null && coverage.missing_sources !== missing.size) fail();
  if (coverage.expected_sources !== null && coverage.missing_sources !== null
      && coverage.expected_sources !== coverage.covered_sources + coverage.missing_sources) fail();
  for (const [section, key] of [['attempts', 'attempt_id'], ['intervals', 'interval_id'], ['rounds', 'round_id']]) {
    if (new Set(payload[section].map(row => row[key])).size !== payload[section].length) fail();
  }
  for (const [section, rows] of [
    ['attempts', payload.attempts], ['intervals', payload.intervals], ['rounds', payload.rounds],
    ['usage.requests', payload.usage.requests], ['cost.applied_rates', payload.cost.applied_rates ?? []]
  ]) {
    for (const [index, row] of rows.entries()) {
      if (Object.hasOwn(row, 'start') && row.end !== null && instant(row.end) < instant(row.start)) {
        throw Object.assign(new Error('invalid_publication_payload'), {
          validation_error: 'end_before_start', validation_path: `${section}[${index}].end`
        });
      }
    }
  }
  const actors = new Set(payload.attempts.map(row => row.actor_id));
  for (const [index, row] of payload.intervals.entries()) {
    if (row.scope === 'actor' && (row.actor_id === null || !actors.has(row.actor_id))
        || row.scope === 'task' && row.actor_id !== null) {
      throw Object.assign(new Error('invalid_publication_payload'), {
        validation_error: 'unknown_actor', validation_path: `intervals[${index}].actor_id`
      });
    }
  }
  return payload;
}
