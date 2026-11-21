import { AED_REPORT_DATASET_TITLE } from '@app/pages/aed-campaign/aed-campaign.brand';

/**
 * True when a search result title names the national "Raport zbiorczy AED" dataset.
 * The portal search API highlights matches with <mark> tags, so tags are removed before comparing.
 */
export function isReportDatasetTitle(title: string | null | undefined): boolean {
  const text = (title || '')
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
  return text.includes(AED_REPORT_DATASET_TITLE.toLowerCase());
}

/** True for the OpenStreetMap resource of the report. */
export function isOsmResource(title: string | null | undefined): boolean {
  return /\bosm\b|openstreetmap/i.test(title || '');
}
