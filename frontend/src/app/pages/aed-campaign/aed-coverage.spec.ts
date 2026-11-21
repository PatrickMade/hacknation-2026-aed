import { computeCoverage, GminaFeature, normalizeTerc } from './aed-coverage';

const square = (terc: string, name: string, x0: number, y0: number): GminaFeature => ({
  type: 'Feature',
  properties: { terc, name },
  geometry: {
    type: 'Polygon',
    coordinates: [
      [
        [x0, y0],
        [x0 + 1, y0],
        [x0 + 1, y0 + 1],
        [x0, y0 + 1],
        [x0, y0],
      ],
    ],
  },
});

const gminy = [
  square('1465011', 'Warszawa', 21, 52),
  square('1408011', 'Legionowo', 20, 52),
  square('1861011', 'Krosno', 22, 49),
];

describe('normalizeTerc', () => {
  it('keeps a 7-digit gmina code and maps urban-rural parts to the gmina', () => {
    expect(normalizeTerc('1408011')).toBe('1408011');
    expect(normalizeTerc(' 0201044 ')).toBe('0201043');
    expect(normalizeTerc('0201045')).toBe('0201043');
    expect(normalizeTerc('201044')).toBe('0201043');
    expect(normalizeTerc(201011)).toBe('0201011');
    expect(normalizeTerc('14')).toBeNull();
    expect(normalizeTerc(null)).toBeNull();
  });
});

describe('computeCoverage', () => {
  const records = [
    { terc: '1465011', operatorName: 'Urząd m.st. Warszawy', publishers: [], lat: 52.2, lon: 21.0 + 0.5 },
    { terc: '1465011', operatorName: 'Urząd m.st. Warszawy', publishers: [], lat: 52.3, lon: 21.4 },
    { terc: '1465088', operatorName: 'Szkoła Podstawowa nr 1', publishers: [], lat: 52.5, lon: 21.5 },
    { terc: '', operatorName: 'Gmina Miejska Legionowo', publishers: [], lat: 52.5, lon: 20.5 },
    { terc: '', operatorName: 'Bez pozycji', publishers: [], lat: null, lon: null },
  ];
  const osm = [
    { lat: 52.5, lon: 21.5 },
    { lat: 49.5, lon: 22.5 },
    { lat: 49.6, lon: 22.6 },
    { lat: 10, lon: 10 },
  ];

  it('counts operators, records and covered gminy from official records', () => {
    const result = computeCoverage(records, osm, gminy);

    expect(result.records).toBe(5);
    expect(result.confirmedOperators).toBe(4);
    expect(result.gminyCovered).toBe(2);
    expect(result.gminyTotal).toBe(3);
  });

  it('classifies gminy as published, gap (OSM only) or none', () => {
    const result = computeCoverage(records, osm, gminy);
    const warszawa = result.gminy.get('1465011');

    expect(warszawa.status).toBe('published');
    expect(warszawa.officialCount).toBe(3);
    expect(warszawa.operators).toEqual(['Szkoła Podstawowa nr 1', 'Urząd m.st. Warszawy']);
    expect(warszawa.osmCount).toBe(1);
    expect(result.gminy.get('1408011').status).toBe('published');
    expect(result.gminy.get('1861011')).toEqual(
      expect.objectContaining({ status: 'gap', officialCount: 0, osmCount: 2, name: 'Krosno' }),
    );
    expect(result.gaps).toBe(1);
  });

  it('assigns gminy from coordinates when the report has no terc column', () => {
    const withoutTerc = [
      { terc: null, operatorName: 'Gmina Miejska Krosno', publishers: [], lat: 49.7, lon: 22.8 },
      { terc: null, operatorName: 'Gmina Miejska Krosno', publishers: [], lat: 49.6, lon: 22.7 },
      { terc: null, operatorName: 'Urząd Miasta Legionowo', publishers: [], lat: 52.4, lon: 20.9 },
      { terc: null, operatorName: 'Urząd Miasta Legionowo', publishers: [], lat: null, lon: null },
    ];
    const result = computeCoverage(withoutTerc, [], gminy);

    expect(result.records).toBe(4);
    expect(result.confirmedOperators).toBe(2);
    expect(result.gminyCovered).toBe(2);
    expect(result.gminy.get('1861011').officialCount).toBe(2);
    expect(result.gminy.get('1408011').officialCount).toBe(1);
  });

  it('counts data publishers and confirmed dysponenci separately (L4 compliance contract)', () => {
    const compliance = [
      { terc: '1408011', operatorName: 'nieustalony', publishers: ['Urząd Miasta Legionowo'], lat: 52.4, lon: 20.5 },
      { terc: '1408011', operatorName: 'nieustalony', publishers: ['Urząd Miasta Legionowo'], lat: 52.5, lon: 20.4 },
      { terc: '1861011', operatorName: 'nieustalony', publishers: ['Urząd Miasta Krosna'], lat: 49.7, lon: 22.8 },
      {
        terc: '1861011',
        operatorName: 'Szpital Wojewódzki w Krośnie',
        publishers: ['Urząd Miasta Krosna'],
        lat: 49.6,
        lon: 22.7,
      },
      { terc: '1465011', operatorName: '', publishers: [], lat: 52.2, lon: 21.5 },
    ];
    const result = computeCoverage(compliance, [], gminy);

    expect(result.records).toBe(5);
    expect(result.publishers).toBe(2);
    expect(result.confirmedOperators).toBe(1);
    expect(result.gminy.get('1408011').publishers).toEqual(['Urząd Miasta Legionowo']);
    expect(result.gminy.get('1861011').publishers).toEqual(['Urząd Miasta Krosna']);
    expect(result.gminy.get('1861011').operators).toEqual(['Szpital Wojewódzki w Krośnie']);
    expect(result.gminy.get('1408011').operators).toEqual([]);
    expect(result.gminy.get('1465011').publishers).toEqual([]);
    expect(result.gminyCovered).toBe(3);
  });

  it('never counts "nieustalony" variants as a confirmed dysponent', () => {
    const records = ['nieustalony', 'Nieustalony', 'nieustalony (OpenStreetMap)', '  '].map((operatorName) => ({
      terc: '1408011',
      operatorName,
      publishers: [],
      lat: 52.4,
      lon: 20.5,
    }));

    expect(computeCoverage(records, [], gminy).confirmedOperators).toBe(0);
  });

  it('returns no covered gminy without records', () => {
    const result = computeCoverage([], [], gminy);

    expect(result.records).toBe(0);
    expect(result.gminyCovered).toBe(0);
    expect(result.gminy.get('1465011').status).toBe('none');
  });
});
