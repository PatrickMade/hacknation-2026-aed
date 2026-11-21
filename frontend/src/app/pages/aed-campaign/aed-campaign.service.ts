import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, from, Observable, of } from 'rxjs';
import { concatMap, map, mergeMap, switchMap, toArray } from 'rxjs/operators';

import { AED_REPORT_DATASET_TITLE } from '@app/pages/aed-campaign/aed-campaign.brand';
import { AedOfficialRecord, AedPoint, GminaFeature } from '@app/pages/aed-campaign/aed-coverage';
import {
  isOsmDatasetTitle,
  isOsmResource,
  isReportDatasetTitle,
  publishersFromSourceRecords,
} from '@app/pages/aed-campaign/aed-report-lookup';
import { ApiModel } from '@app/services/api/api-model';
import { DatasetService } from '@app/services/dataset.service';

/** Page size limit of the portal table API. */
const PAGE_SIZE = 100;
/** Elasticsearch result window of one resource data index: a query can page through at most this many rows. */
const ROW_WINDOW = 10000;
/** Latitude bands (degrees) for reading a larger resource; Poland lies within 49-55 N. */
const LATITUDE_BANDS: [number, number][] = [49, 50, 51, 52, 53, 54].map((lat) => [lat, lat + 1]);
/** Narrowest band that is still split in two when it holds more rows than the window. */
const MIN_BAND = 0.01;
const PARALLEL_REQUESTS = 6;

export interface AedReportData {
  datasetId: string;
  datasetSlug: string;
  dataDate: string | null;
  /** True when some rows could not be read within the portal's row window. */
  truncated: boolean;
  records: AedOfficialRecord[];
  /** OpenStreetMap resource of the report, read separately with getOsmPoints(). */
  osmResourceId: string | null;
}

export interface AedOsmData {
  points: AedPoint[];
  /** True when some rows could not be read within the portal's row window. */
  truncated: boolean;
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
        map((response) => response.results.find((item) => isReportDatasetTitle(item.attributes?.title))),
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
          osmResourceId: osm ? of(String(osm.id)) : this.findOsmResource(),
        }).pipe(
          map(({ official: { rows, truncated }, osmResourceId }) => ({
            datasetId: String(dataset.id),
            datasetSlug: dataset.attributes?.slug,
            dataDate: official.attributes?.data_date || dataset.attributes?.modified || null,
            truncated,
            records: rows.map((row) => ({
              // 7-digit gmina code from PRG; when missing or unknown, the gmina comes from coordinates.
              terc: row['terc'] ?? null,
              operatorName: row['operator_name'],
              publishers: publishersFromSourceRecords(row['source_records']),
              lat: toNumber(row['latitude']),
              lon: toNumber(row['longitude']),
            })),
            osmResourceId,
          })),
        );
      }),
    );
  }

  /** The CSV resource of the separate OpenStreetMap AED dataset, or null when there is none. */
  private findOsmResource(): Observable<string | null> {
    return this.datasetService.getAll({ q: 'AED OpenStreetMap', 'model[terms]': ApiModel.DATASET, per_page: 10 }).pipe(
      map((response) => response.results.find((item) => isOsmDatasetTitle(item.attributes?.title))),
      switchMap((dataset) =>
        dataset
          ? this.datasetService.getResourcesList(dataset.id, { per_page: 100 }).pipe(
              map((response) => {
                const resource = (response.results || []).find(
                  (item) => (item.attributes?.format || '').toLowerCase() === 'csv',
                );
                return resource ? String(resource.id) : null;
              }),
            )
          : of(null),
      ),
    );
  }

  /** Points of the OpenStreetMap resource; it is large, so the page reads it after the counters are shown. */
  getOsmPoints(resourceId: string): Observable<AedOsmData> {
    return this.getRows(resourceId).pipe(
      map(({ rows, truncated }) => ({
        points: rows
          .map((row) => ({
            lat: toNumber(row['latitude'] ?? row['lat']),
            lon: toNumber(row['longitude'] ?? row['lon']),
          }))
          .filter((point) => point.lat !== null && point.lon !== null),
        truncated,
      })),
    );
  }

  /**
   * Reads every row of a tabular resource, page by page, with column names from `meta.headers_map`.
   * A resource larger than the row window is read in latitude bands (`q=colN:[a TO b}`), each within the window.
   */
  private getRows(resourceId: string): Observable<{ rows: Row[]; truncated: boolean }> {
    return this.readQuery(resourceId).pipe(
      switchMap((result) => {
        if (!result.overflow) {
          return of({ rows: result.rows, truncated: false });
        }
        const latitude = Object.entries(result.headers).find(([, name]) => name === 'latitude' || name === 'lat');
        if (!latitude) {
          return of({ rows: result.rows, truncated: true });
        }
        const column = latitude[0];
        const queries = [
          `${column}:<${LATITUDE_BANDS[0][0]}`,
          `${column}:>=${LATITUDE_BANDS[LATITUDE_BANDS.length - 1][1]}`,
        ];
        return from(LATITUDE_BANDS).pipe(
          concatMap(([low, high]) => this.readBand(resourceId, column, low, high)),
          toArray(),
          switchMap((bands) =>
            from(queries).pipe(
              concatMap((query) => this.readQuery(resourceId, query)),
              toArray(),
              map((edges) => ({
                rows: [...bands.flatMap((band) => band.rows), ...edges.flatMap((edge) => edge.rows)],
                truncated: bands.some((band) => band.truncated) || edges.some((edge) => edge.overflow),
              })),
            ),
          ),
        );
      }),
    );
  }

  /** Reads one latitude band, halving it while it holds more rows than the window. */
  private readBand(
    resourceId: string,
    column: string,
    low: number,
    high: number,
  ): Observable<{ rows: Row[]; truncated: boolean }> {
    return this.readQuery(resourceId, `${column}:[${low} TO ${high}}`).pipe(
      switchMap((result) => {
        if (!result.overflow) {
          return of({ rows: result.rows, truncated: false });
        }
        if (high - low < MIN_BAND) {
          return of({ rows: result.rows, truncated: true });
        }
        const middle = Math.round(((low + high) / 2) * 10000) / 10000;
        return from([
          [low, middle],
          [middle, high],
        ]).pipe(
          concatMap(([from_, to]) => this.readBand(resourceId, column, from_, to)),
          toArray(),
          map((halves) => ({
            rows: halves.flatMap((half) => half.rows),
            truncated: halves.some((half) => half.truncated),
          })),
        );
      }),
    );
  }

  /** Reads all pages of one query that fit the row window; `overflow` means the query matched more rows. */
  private readQuery(
    resourceId: string,
    query?: string,
  ): Observable<{ rows: Row[]; headers: Record<string, string>; overflow: boolean }> {
    const page = (number: number) =>
      this.datasetService.getResourceData(resourceId, {
        page: String(number),
        per_page: String(PAGE_SIZE),
        ...(query ? { q: query } : {}),
      });

    return page(1).pipe(
      switchMap((first: TableResponse) => {
        const count = first?.meta?.count || 0;
        if (count > ROW_WINDOW) {
          return of({ rows: [], headers: first?.meta?.headers_map || {}, overflow: true });
        }
        const pages = Math.ceil(count / PAGE_SIZE);
        const rest = Array.from({ length: Math.max(pages - 1, 0) }, (_, index) => index + 2);
        return from(rest).pipe(
          mergeMap((number) => page(number), PARALLEL_REQUESTS),
          toArray(),
          map((responses: TableResponse[]) => ({
            rows: [first, ...responses].flatMap((response) => this.toRows(response)),
            headers: first?.meta?.headers_map || {},
            overflow: false,
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
