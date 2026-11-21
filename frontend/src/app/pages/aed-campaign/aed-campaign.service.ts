import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, from, Observable, of } from 'rxjs';
import { map, mergeMap, switchMap, toArray } from 'rxjs/operators';

import { AED_REPORT_DATASET_TITLE } from '@app/pages/aed-campaign/aed-campaign.brand';
import { AedOfficialRecord, AedPoint, GminaFeature } from '@app/pages/aed-campaign/aed-coverage';
import { ApiModel } from '@app/services/api/api-model';
import { DatasetService } from '@app/services/dataset.service';

/** Page size limit of the portal table API. */
const PAGE_SIZE = 100;
/** Elasticsearch result window of the portal (max_result_window). */
const MAX_ROWS = 40000;
const PARALLEL_REQUESTS = 6;

export interface AedReportData {
  datasetId: string;
  datasetSlug: string;
  dataDate: string | null;
  /** True when a resource has more rows than the portal returns (MAX_ROWS). */
  truncated: boolean;
  records: AedOfficialRecord[];
  osmPoints: AedPoint[];
}

type Row = Record<string, string | null>;

interface ApiItem {
  id: string;
  attributes?: { title?: string; slug?: string; format?: string; data_date?: string; modified?: string };
}

interface TableResponse {
  data?: { attributes?: Record<string, unknown> }[];
  meta?: { count?: number; headers_map?: Record<string, string> };
}

function cellValue(raw: unknown): string | null {
  if (raw === null || raw === undefined) {
    return null;
  }
  const value = typeof raw === 'object' ? (raw as { val?: unknown }).val : raw;
  return value === null || value === undefined ? null : String(value);
}

function toNumber(value: string | null): number | null {
  if (value === null || value.trim() === '') {
    return null;
  }
  const parsed = Number(value.replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : null;
}

function isOsmResource(title: string): boolean {
  return /\bosm\b|openstreetmap/i.test(title || '');
}

/**
 * Reads the "Raport zbiorczy AED" dataset through the public portal API.
 */
@Injectable({ providedIn: 'root' })
export class AedCampaignService {
  constructor(
    private datasetService: DatasetService,
    private http: HttpClient,
  ) {}

  /** Simplified gmina boundaries (PRG, GUGiK) bundled with the frontend. */
  getGminy(): Observable<GminaFeature[]> {
    return this.http
      .get<{ features: GminaFeature[] }>('/assets/aed/gminy.geojson')
      .pipe(map((collection) => collection.features));
  }

  /** Returns null when the report dataset or its official resource is not published yet. */
  getReport(): Observable<AedReportData | null> {
    return this.datasetService
      .getAll({ q: AED_REPORT_DATASET_TITLE, 'model[terms]': ApiModel.DATASET, per_page: 10 })
      .pipe(
        map((response) =>
          response.results.find((item) =>
            (item.attributes?.title || '').toLowerCase().includes(AED_REPORT_DATASET_TITLE.toLowerCase()),
          ),
        ),
        switchMap((dataset) => (dataset ? this.readDataset(dataset) : of(null))),
      );
  }

  private readDataset(dataset: ApiItem): Observable<AedReportData | null> {
    return this.datasetService.getResourcesList(dataset.id, { per_page: 100 }).pipe(
      switchMap((response) => {
        const resources = response.results || [];
        const official = resources.find(
          (item) => !isOsmResource(item.attributes?.title) && (item.attributes?.format || '').toLowerCase() === 'csv',
        );
        if (!official) {
          return of(null);
        }
        const osm = resources.find((item) => isOsmResource(item.attributes?.title));
        return forkJoin({
          official: this.getRows(official.id),
          osm: osm ? this.getRows(osm.id) : of({ rows: [] as Row[], truncated: false }),
        }).pipe(
          map(({ official: { rows: records, truncated }, osm: { rows: osmRows, truncated: osmTruncated } }) => ({
            datasetId: String(dataset.id),
            datasetSlug: dataset.attributes?.slug,
            dataDate: official.attributes?.data_date || dataset.attributes?.modified || null,
            truncated: truncated || osmTruncated,
            records: records.map((row) => ({
              // Optional: the raport zbiorczy has no terc column, so the gmina usually comes from coordinates.
              terc: row['terc'] ?? null,
              operatorName: row['operator_name'],
              lat: toNumber(row['latitude']),
              lon: toNumber(row['longitude']),
            })),
            osmPoints: osmRows
              .map((row) => ({
                lat: toNumber(row['latitude'] ?? row['lat']),
                lon: toNumber(row['longitude'] ?? row['lon']),
              }))
              .filter((point) => point.lat !== null && point.lon !== null),
          })),
        );
      }),
    );
  }

  /** Reads every row of a tabular resource, page by page, with column names from `meta.headers_map`. */
  private getRows(resourceId: string): Observable<{ rows: Row[]; truncated: boolean }> {
    const page = (number: number) =>
      this.datasetService.getResourceData(resourceId, { page: String(number), per_page: String(PAGE_SIZE) });

    return page(1).pipe(
      switchMap((first) => {
        const pages = Math.ceil(Math.min(first?.meta?.count || 0, MAX_ROWS) / PAGE_SIZE);
        const rest = Array.from({ length: Math.max(pages - 1, 0) }, (_, index) => index + 2);
        return from(rest).pipe(
          mergeMap((number) => page(number), PARALLEL_REQUESTS),
          toArray(),
          map((responses) => ({
            rows: [first, ...responses].flatMap((response) => this.toRows(response)),
            truncated: (first?.meta?.count || 0) > MAX_ROWS,
          })),
        );
      }),
    );
  }

  private toRows(response: TableResponse): Row[] {
    const headers: Record<string, string> = response?.meta?.headers_map || {};
    return (response?.data || []).map((item) => {
      const row: Row = {};
      Object.entries(headers).forEach(([column, name]) => (row[name] = cellValue(item.attributes?.[column])));
      return row;
    });
  }
}
