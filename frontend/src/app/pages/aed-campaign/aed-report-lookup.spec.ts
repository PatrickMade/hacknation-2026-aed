import { isOsmResource, isReportDatasetTitle } from './aed-report-lookup';

describe('isReportDatasetTitle', () => {
  it('matches the plain dataset title', () => {
    expect(isReportDatasetTitle('Raport zbiorczy AED')).toBe(true);
  });

  it('matches the title with search highlight markup from the portal search API', () => {
    expect(isReportDatasetTitle('<mark>Raport</mark> <mark>zbiorczy</mark> <mark>AED</mark></mark>')).toBe(true);
  });

  it('rejects other AED datasets', () => {
    expect(isReportDatasetTitle('Defibrylatory <mark>AED</mark> - Dysponent demonstracyjny</mark>')).toBe(false);
    expect(isReportDatasetTitle(undefined)).toBe(false);
  });
});

describe('isOsmResource', () => {
  it('recognises the published resources', () => {
    expect(isOsmResource('Punkty AED z OpenStreetMap - Polska (ODbL 1.0)')).toBe(true);
    expect(isOsmResource('Raport zbiorczy AED (CSV)')).toBe(false);
    expect(isOsmResource('Raport zbiorczy AED (GeoJSON)')).toBe(false);
  });
});
