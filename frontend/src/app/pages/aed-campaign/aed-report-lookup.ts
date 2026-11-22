import { AED_REPORT_DATASET_TITLE } from '@app/pages/aed-campaign/aed-campaign.brand';

/**
 * True when a search result title names the national "Raport zbiorczy AED" dataset.
 * The portal search API highlights matches with <mark> tags, so tags are removed before comparing.
 */
export function isReportDatasetTitle(title: string | null | undefined): boolean {
  return plainTitle(title).includes(AED_REPORT_DATASET_TITLE.toLowerCase());
}

/** True for the separate OpenStreetMap AED dataset (L4 compliance: OSM has its own dataset with ODbL licence). */
export function isOsmDatasetTitle(title: string | null | undefined): boolean {
  const text = plainTitle(title);
  return text.includes('openstreetmap') && /\baed\b/.test(text);
}

const DYSPONENT_SOURCE_PREFIX = 'dysponent:';

/**
 * Data publishers of one record: unique `publisher_name` values from the `source_records` JSON cell.
 * A dysponent's own publication (source_id "dysponent:…", provider wizard or seed_aed_demo) has no
 * publisher_name in L4's output: the dysponent publishes it, so its operator name is the publisher.
 * An unreadable cell gives no publishers rather than failing the page.
 */
export function publishersFromSourceRecords(cell: string | null | undefined, operatorName?: string | null): string[] {
  const names = parseJsonArray(cell)
    .filter((entry): entry is SourceEntry => !!entry && typeof entry === 'object')
    .map((entry) => {
      if (typeof entry.publisher_name === 'string' && entry.publisher_name.trim() !== '') {
        return entry.publisher_name.trim();
      }
      return isDysponentSource(entry) && hasOperatorName(operatorName) ? operatorName.trim() : null;
    })
    .filter((name): name is string => !!name);
  return Array.from(new Set(names));
}

/**
 * L4 contract: a record's dysponent is confirmed when a source is a dysponent publication (source_id
 * "dysponent:…", the provider wizard) or when readable quality flags do not mark the name as unconfirmed
 * (operator_from_location: taken from the source's location text; operator_unconfirmed: OSM candidate).
 * Missing or unreadable flags are no evidence, so they do not confirm the dysponent.
 */
export function hasConfirmedOperator(
  sourceRecordsCell: string | null | undefined,
  flagsCell: string | null | undefined,
): boolean {
  const fromDysponent = parseJsonArray(sourceRecordsCell).some(
    (entry) => !!entry && typeof entry === 'object' && isDysponentSource(entry as SourceEntry),
  );
  if (fromDysponent) {
    return true;
  }
  const flags = readJsonArray(flagsCell);
  if (!flags) {
    return false;
  }
  const names = flags.map(String);
  return !names.includes('operator_from_location') && !names.includes('operator_unconfirmed');
}

/** True for a real operator name: not empty and not a "nieustalony" placeholder (e.g. "nieustalony (OpenStreetMap)"). */
export function hasOperatorName(name: string | null | undefined): boolean {
  const text = (name || '').trim();
  return text !== '' && !/^nieustalony/i.test(text);
}

interface SourceEntry {
  source_id?: unknown;
  publisher_name?: unknown;
}

function isDysponentSource(entry: SourceEntry): boolean {
  return String(entry.source_id || '').startsWith(DYSPONENT_SOURCE_PREFIX);
}

/** Parsed JSON array, or null when the cell is empty, not JSON or not an array. */
function readJsonArray(cell: string | null | undefined): unknown[] | null {
  if (!cell || !cell.trim()) {
    return null;
  }
  try {
    const value = JSON.parse(cell);
    return Array.isArray(value) ? value : null;
  } catch {
    return null;
  }
}

function parseJsonArray(cell: string | null | undefined): unknown[] {
  return readJsonArray(cell) || [];
}

/** Title without the search API's <mark> highlight tags, lower case, single spaces. */
function plainTitle(title: string | null | undefined): string {
  return (title || '')
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

/** True for the OpenStreetMap resource of the report. */
export function isOsmResource(title: string | null | undefined): boolean {
  return /\bosm\b|openstreetmap/i.test(title || '');
}
