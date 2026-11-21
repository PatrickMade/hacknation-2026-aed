import { Observable, of, throwError } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { AedCampaignService } from './aed-campaign.service';

/** Portal table API fake: 100 rows per page and a 10000-row Elasticsearch window per query. */
function tableApi(rows: Record<string, string | number>[], params: Record<string, string>): Observable<unknown> {
  const columns = Object.keys(rows[0]);
  let selected = rows;
  const range = /^col(\d+):\[(\S+) TO (\S+)\}$/.exec(params['q'] || '');
  const below = /^col(\d+):<(\S+)$/.exec(params['q'] || '');
  const above = /^col(\d+):>=(\S+)$/.exec(params['q'] || '');
  const value = (row: Record<string, string | number>, index: string) => Number(row[columns[Number(index) - 1]]);
  if (range) {
    selected = rows.filter(
      (row) => value(row, range[1]) >= Number(range[2]) && value(row, range[1]) < Number(range[3]),
    );
  } else if (below) {
    selected = rows.filter((row) => value(row, below[1]) < Number(below[2]));
  } else if (above) {
    selected = rows.filter((row) => value(row, above[1]) >= Number(above[2]));
  }
  const page = Number(params['page']);
  const perPage = Number(params['per_page']);
  if (page * perPage > 10000) {
    return throwError(() => ({ status: 400, detail: 'all shards failed' }));
  }
  const chunk = selected.slice((page - 1) * perPage, page * perPage);
  return of({
    data: chunk.map((row) => ({
      attributes: Object.fromEntries(columns.map((column, index) => [`col${index + 1}`, { val: row[column] }])),
    })),
    meta: {
      count: selected.length,
      headers_map: Object.fromEntries(columns.map((column, index) => [`col${index + 1}`, column])),
    },
  });
}

describe('AedCampaignService.getReport', () => {
  const official = [
    { operator_name: 'Urząd Miasta Marki', latitude: 52.32, longitude: 21.11 },
    { operator_name: 'Gmina Miejska Krosno', latitude: 49.69, longitude: 21.77 },
  ];
  const osm = Array.from({ length: 25000 }, (_, index) => ({
    aed_id: `osm-${index}`,
    latitude: 49 + (index % 6000) / 1000,
    longitude: 14.5 + (index % 900) / 100,
  }));

  const datasetService = {
    getAll: () =>
      of({
        results: [
          { id: '6', attributes: { title: '<mark>Raport</mark> <mark>zbiorczy</mark> <mark>AED</mark></mark>' } },
        ],
      }),
    getResourcesList: () =>
      of({
        results: [
          { id: '7', attributes: { title: 'Raport zbiorczy AED (GeoJSON)', format: 'geojson' } },
          { id: '8', attributes: { title: 'Punkty AED z OpenStreetMap - Polska (ODbL 1.0)', format: 'csv' } },
          { id: '6', attributes: { title: 'Raport zbiorczy AED (CSV)', format: 'csv', data_date: '2026-11-21' } },
        ],
      }),
    getResourceData: (id: string, params: Record<string, string>) => tableApi(id === '8' ? osm : official, params),
  };

  it('reads every OSM row of a resource larger than the 10000-row window', (done) => {
    const service = new AedCampaignService(datasetService as never, {} as never);

    service
      .getReport()
      .pipe(
        switchMap((report) => {
          expect(report.records.length).toBe(2);
          expect(report.truncated).toBe(false);
          expect(report.osmResourceId).toBe('8');
          return service.getOsmPoints(report.osmResourceId);
        }),
      )
      .subscribe({
        next: (osmData) => {
          expect(osmData.points.length).toBe(25000);
          expect(osmData.truncated).toBe(false);
          done();
        },
        error: (error) => done(error),
      });
  });
});
