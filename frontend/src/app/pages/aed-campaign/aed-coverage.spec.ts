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
    expect(normalizeTerc('14')).toBeNull();
    expect(normalizeTerc(null)).toBeNull();
  });
});

describe('computeCoverage', () => {
  const records = [
    { terc: '1465011', operatorName: 'Urząd m.st. Warszawy', lat: 52.2, lon: 21.0 + 0.5 },
    { terc: '1465011', operatorName: 'Urząd m.st. Warszawy', lat: 52.3, lon: 21.4 },
    { terc: '1465088', operatorName: 'Szkoła Podstawowa nr 1', lat: 52.5, lon: 21.5 },
    { terc: '', operatorName: 'Gmina Miejska Legionowo', lat: 52.5, lon: 20.5 },
    { terc: '', operatorName: 'Bez pozycji', lat: null, lon: null },
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
    expect(result.operators).toBe(4);
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

  it('returns no covered gminy without records', () => {
    const result = computeCoverage([], [], gminy);

    expect(result.records).toBe(0);
    expect(result.gminyCovered).toBe(0);
    expect(result.gminy.get('1465011').status).toBe('none');
  });
});
