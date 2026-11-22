import {
  hasConfirmedOperator,
  isOsmResource,
  isReportDatasetTitle,
  publishersFromSourceRecords,
} from './aed-report-lookup';

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

describe('publishersFromSourceRecords', () => {
  it('names the dysponent as the publisher of its own publication, which has no publisher_name (L4 demo/wizard)', () => {
    const cell = JSON.stringify([
      { source_id: 'dane.gov.pl:1', publisher_name: 'Urząd Miasta Lublin' },
      { source_id: 'dysponent:demo-szpital', source_record_id: 'DEMO-1' },
    ]);

    expect(publishersFromSourceRecords(cell, ' Szpital Demonstracyjny ')).toEqual([
      'Urząd Miasta Lublin',
      'Szpital Demonstracyjny',
    ]);
  });

  it('gives no publisher for a dysponent source when the record has no real operator name', () => {
    const cell = JSON.stringify([{ source_id: 'dysponent:demo-szpital' }]);

    expect(publishersFromSourceRecords(cell, '')).toEqual([]);
    expect(publishersFromSourceRecords(cell, 'nieustalony')).toEqual([]);
  });

  it('does not use the operator name for municipal sources without publisher_name', () => {
    expect(publishersFromSourceRecords(JSON.stringify([{ source_id: 'dane.gov.pl:1' }]), 'Szkoła nr 1')).toEqual([]);
  });
});

describe('hasConfirmedOperator', () => {
  const municipal = JSON.stringify([{ source_id: 'dane.gov.pl:1', publisher_name: 'Urząd Miasta Lublin' }]);
  const dysponent = JSON.stringify([{ source_id: 'dysponent:demo-szpital' }]);

  it('treats unreadable or missing quality flags as not confirmed', () => {
    expect(hasConfirmedOperator(municipal, 'not json')).toBe(false);
    expect(hasConfirmedOperator(municipal, '{"a":1}')).toBe(false);
    expect(hasConfirmedOperator(municipal, null)).toBe(false);
    expect(hasConfirmedOperator(municipal, '')).toBe(false);
  });

  it('confirms a dysponent source even when the flags are unreadable', () => {
    expect(hasConfirmedOperator(dysponent, 'not json')).toBe(true);
  });

  it('confirms readable flags without operator_from_location and operator_unconfirmed', () => {
    expect(hasConfirmedOperator(municipal, '[]')).toBe(true);
    expect(hasConfirmedOperator(municipal, '["operator_from_location"]')).toBe(false);
    expect(hasConfirmedOperator(municipal, '["operator_unconfirmed"]')).toBe(false);
  });
});
