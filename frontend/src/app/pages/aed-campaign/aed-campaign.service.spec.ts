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
        results: [{ id: '6', attributes: { title: '<mark>Raport</mark> <mark>zbiorczy</mark> <mark>AED</mark>' } }],
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

  it('reads publishers from source_records and finds OSM in its own dataset (L4 compliance contract)', (done) => {
    const sourceRecords = (publisher: string) =>
      JSON.stringify([{ source_id: 'dane.gov.pl', publisher_name: publisher, source_url: 'https://example.org' }]);
    const flags = (...names: string[]) => JSON.stringify(names);
    // L4 demo.py / wizard shape: a dysponent's own publication has no publisher_name.
    const demo = JSON.stringify([
      {
        source_id: 'dysponent:demo-1',
        source_record_id: 'DEMO-1',
        source_url: 'https://mcod.local/pl/dataset',
        retrieved_at: '2026-11-22T00:00:00Z',
        license_url: 'https://creativecommons.org/publicdomain/zero/1.0/',
        attribution: 'Przychodnia Zdrowie (dane demonstracyjne) - dane demonstracyjne',
      },
    ]);
    const compliance = [
      {
        operator_name: 'Szkoła Podstawowa nr 1',
        terc: '1434011',
        source_records: sourceRecords('Urząd Miasta Marki'),
        quality_flags: flags('operator_from_location'),
        latitude: 52.32,
        longitude: 21.11,
      },
      {
        operator_name: 'Urząd Miasta Krosna',
        terc: '1861011',
        source_records: sourceRecords('Urząd Miasta Krosna'),
        quality_flags: flags('operator_from_location', 'encoded_csv'),
        latitude: 49.69,
        longitude: 21.77,
      },
      {
        operator_name: 'Hala sportowa',
        terc: '1861011',
        source_records: 'not json',
        quality_flags: 'not json',
        latitude: 49.68,
        longitude: 21.76,
      },
      {
        operator_name: 'Przychodnia Zdrowie (dane demonstracyjne)',
        terc: '1408011',
        source_records: demo,
        quality_flags: flags(),
        latitude: 52.4,
        longitude: 20.9,
      },
    ];
    const osmPoints = [{ aed_id: 'osm-1', latitude: 52.2, longitude: 21.0 }];
    const complianceApi = {
      getAll: (params: Record<string, string>) =>
        of({
          results: /openstreetmap/i.test(params['q'])
            ? [{ id: '9', attributes: { title: 'Punkty AED z <mark>OpenStreetMap</mark> - Polska (ODbL 1.0)' } }]
            : [{ id: '6', attributes: { title: '<mark>Raport</mark> <mark>zbiorczy</mark> <mark>AED</mark>' } }],
        }),
      getResourcesList: (datasetId: string) =>
        of({
          results:
            datasetId === '9'
              ? [{ id: '11', attributes: { title: 'Punkty AED z OpenStreetMap - Polska', format: 'csv' } }]
              : [
                  { id: '7', attributes: { title: 'Raport zbiorczy AED (GeoJSON)', format: 'geojson' } },
                  { id: '6', attributes: { title: 'Raport zbiorczy AED (CSV)', format: 'csv' } },
                ],
        }),
      getResourceData: (id: string, params: Record<string, string>) =>
        tableApi(id === '11' ? osmPoints : compliance, params),
    };
    const service = new AedCampaignService(complianceApi as never, {} as never);

    service.getReport().subscribe({
      next: (report) => {
        expect(report.records.map((record) => record.publishers)).toEqual([
          ['Urząd Miasta Marki'],
          ['Urząd Miasta Krosna'],
          [],
          ['Przychodnia Zdrowie (dane demonstracyjne)'],
        ]);
        // Unreadable quality_flags give no evidence, so "Hala sportowa" is not a confirmed dysponent.
        expect(report.records.map((record) => record.confirmedOperator)).toEqual([false, false, false, true]);
        expect(report.records[0].terc).toBe('1434011');
        expect(report.records.map((record) => record.demo)).toEqual([false, false, false, true]);
        expect(report.osmResourceId).toBe('11');
        expect(report.osmLookupFailed).toBe(false);
        done();
      },
      error: (error) => done(error),
    });
  });

  it('keeps the official records when the OpenStreetMap dataset lookup fails', (done) => {
    const failingOsmLookup = {
      ...datasetService,
      getAll: (params: Record<string, string>) =>
        /openstreetmap/i.test(params['q']) ? throwError(() => ({ status: 503 })) : datasetService.getAll(),
      getResourcesList: () =>
        of({ results: [{ id: '6', attributes: { title: 'Raport zbiorczy AED (CSV)', format: 'csv' } }] }),
    };
    const service = new AedCampaignService(failingOsmLookup as never, {} as never);

    service.getReport().subscribe({
      next: (report) => {
        expect(report.records.length).toBe(2);
        expect(report.osmResourceId).toBeNull();
        expect(report.osmLookupFailed).toBe(true);
        done();
      },
      error: (error) => done(error),
    });
  });

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
