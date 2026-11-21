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

/**
 * Data publishers of one record: unique `publisher_name` values from the `source_records` JSON cell.
 * An unreadable cell gives no publishers rather than failing the page.
 */
export function publishersFromSourceRecords(cell: string | null | undefined): string[] {
  let entries: unknown;
  try {
    entries = JSON.parse(cell || '[]');
  } catch {
    return [];
  }
  if (!Array.isArray(entries)) {
    return [];
  }
  const names = entries
    .map((entry) =>
      entry && typeof entry === 'object' ? (entry as { publisher_name?: unknown }).publisher_name : null,
    )
    .filter((name): name is string => typeof name === 'string' && name.trim() !== '')
    .map((name) => name.trim());
  return Array.from(new Set(names));
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
