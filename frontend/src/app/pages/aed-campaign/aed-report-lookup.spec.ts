import {
  hasConfirmedOperator,
  isDemoRecord,
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

describe('isDemoRecord', () => {
  const demoSource = (attribution: string) =>
    JSON.stringify([
      {
        source_id: 'dysponent:demo-szpital-sw-lukasza',
        source_record_id: 'DEMO-1',
        attribution,
      },
    ]);

  it('recognises the source marker written by seed_aed_demo', () => {
    expect(
      isDemoRecord(demoSource('Szpital Demonstracyjny św. Łukasza (dane demonstracyjne) - dane demonstracyjne')),
    ).toBe(true);
  });

  it('does not decide by name: a demo-looking name without the source marker is not demo data', () => {
    const wizard = JSON.stringify([
      { source_id: 'dysponent:szpital', source_record_id: '1', attribution: 'Szpital (dane demonstracyjne)' },
    ]);
    const municipal = JSON.stringify([
      { source_id: 'dane.gov.pl:1', publisher_name: 'Urząd', attribution: 'Urząd - dane demonstracyjne' },
    ]);

    expect(isDemoRecord(wizard)).toBe(false);
    expect(isDemoRecord(municipal)).toBe(false);
    expect(isDemoRecord('not json')).toBe(false);
    expect(isDemoRecord(null)).toBe(false);
  });

  it('counts a record merged with an official source as official, not demo', () => {
    const merged = JSON.stringify([
      { source_id: 'dysponent:demo-szpital', attribution: 'Szpital (dane demonstracyjne) - dane demonstracyjne' },
      { source_id: 'dane.gov.pl:1', publisher_name: 'Urząd Miasta Lublin' },
    ]);

    expect(isDemoRecord(merged)).toBe(false);
  });
});
