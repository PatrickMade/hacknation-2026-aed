/**
 * Coverage of Polish gminy by published AED data (pure functions, no Angular).
 */
import { hasOperatorName } from '@app/pages/aed-campaign/aed-report-lookup';

export interface GminaFeature {
  type: 'Feature';
  properties: { terc: string; name: string };
  geometry: { type: 'Polygon'; coordinates: number[][][] } | { type: 'MultiPolygon'; coordinates: number[][][][] };
}

export interface AedOfficialRecord {
  terc: string | null;
  operatorName: string | null;
  /** Institutions that published the record (source_records[].publisher_name; the dysponent for its own publication). */
  publishers: string[];
  /**
   * False when operator_name is not a confirmed dysponent: L4 fills municipal records from the source's location
   * text (flag operator_from_location) and marks OSM candidates with operator_unconfirmed.
   */
  confirmedOperator: boolean;
  /** Fictional demo record from seed_aed_demo (see isDemoRecord); counted apart from official data. */
  demo?: boolean;
  lat: number | null;
  lon: number | null;
}

export interface AedPoint {
  lat: number;
  lon: number;
}

export type GminaStatus = 'published' | 'demo' | 'gap' | 'none';

export interface GminaCoverage {
  terc: string;
  name: string;
  status: GminaStatus;
  /** Official (non-demo) records in the gmina. */
  officialCount: number;
  /** Demo records from seed_aed_demo in the gmina. */
  demoCount: number;
  /** Confirmed dysponenci (operator_name of records with confirmedOperator) in the gmina. */
  operators: string[];
  /** Data publishers of the official records in the gmina. */
  publishers: string[];
  osmCount: number;
}

export interface CoverageSummary {
  records: number;
  /** Unique data publishers (source_records[].publisher_name). */
  publishers: number;
  /**
   * Unique confirmed dysponenci: operator_name of records with confirmedOperator (L4 rule), skipping empty
   * values and "nieustalony" placeholders.
   */
  confirmedOperators: number;
  /** Demo records from seed_aed_demo, included in records. */
  demoRecords: number;
  /** Publishers that appear only on demo records, included in publishers. */
  demoPublishers: number;
  /** Confirmed dysponenci that appear only on demo records, included in confirmedOperators. */
  demoConfirmedOperators: number;
  /** Gminy with at least one official (non-demo) record. */
  gminyCovered: number;
  /** Gminy with demo records and no official ones (status gap when OSM has points there, otherwise demo). */
  gminyDemoOnly: number;
  /** Number of gminy in the boundary file (PRG). */
  gminyTotal: number;
  gaps: number;
  gminy: Map<string, GminaCoverage>;
}

/**
 * Returns the 7-digit gmina TERC code. Parts of an urban-rural gmina (type 4 and 5) map to the gmina (type 3).
 * A 6-digit value is a code that lost its leading zero.
 */
export function normalizeTerc(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  // A numeric cell drops the leading zero of voivodeship codes 02-08 (e.g. 201011 for 0201011).
  const text = String(value).trim();
  const digits = /^\d{6}$/.test(text) ? '0' + text : text;
  if (!/^\d{7}$/.test(digits)) {
    return null;
  }
  const type = digits[6];
  return type === '4' || type === '5' ? digits.slice(0, 6) + '3' : digits;
}

type Ring = number[][];

function ringContains(ring: Ring, lon: number, lat: number): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

function polygonContains(polygon: Ring[], lon: number, lat: number): boolean {
  if (!ringContains(polygon[0], lon, lat)) {
    return false;
  }
  return !polygon.slice(1).some((hole) => ringContains(hole, lon, lat));
}

interface IndexedGmina {
  terc: string;
  polygons: Ring[][];
  bbox: [number, number, number, number];
}

function indexGminy(gminy: GminaFeature[]): IndexedGmina[] {
  return gminy.map((feature) => {
    const polygons: Ring[][] =
      feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
    const bbox: [number, number, number, number] = [Infinity, Infinity, -Infinity, -Infinity];
    polygons.forEach((polygon) =>
      polygon[0].forEach(([x, y]) => {
        bbox[0] = Math.min(bbox[0], x);
        bbox[1] = Math.min(bbox[1], y);
        bbox[2] = Math.max(bbox[2], x);
        bbox[3] = Math.max(bbox[3], y);
      }),
    );
    return { terc: feature.properties.terc, polygons, bbox };
  });
}

function locate(index: IndexedGmina[], lat: number, lon: number): string | null {
  const hit = index.find(
    (gmina) =>
      lon >= gmina.bbox[0] &&
      lon <= gmina.bbox[2] &&
      lat >= gmina.bbox[1] &&
      lat <= gmina.bbox[3] &&
      gmina.polygons.some((polygon) => polygonContains(polygon, lon, lat)),
  );
  return hit ? hit.terc : null;
}

function isCoordinate(value: number | null): boolean {
  return typeof value === 'number' && Number.isFinite(value);
}

/**
 * Computes counters and per-gmina status. A record's gmina comes from its TERC code when it names a known gmina,
 * otherwise from its coordinates. OSM points are located by coordinates only.
 */
export function computeCoverage(
  records: AedOfficialRecord[],
  osmPoints: AedPoint[],
  gminy: GminaFeature[],
): CoverageSummary {
  const index = indexGminy(gminy);
  const coverage = new Map<string, GminaCoverage>();
  const publishersByGmina = new Map<string, Set<string>>();
  const operatorsByGmina = new Map<string, Set<string>>();
  gminy.forEach((feature) => {
    coverage.set(feature.properties.terc, {
      terc: feature.properties.terc,
      name: feature.properties.name,
      status: 'none',
      officialCount: 0,
      demoCount: 0,
      operators: [],
      publishers: [],
      osmCount: 0,
    });
    publishersByGmina.set(feature.properties.terc, new Set());
    operatorsByGmina.set(feature.properties.terc, new Set());
  });

  const publishers = new Set<string>();
  const officialPublishers = new Set<string>();
  const confirmedOperators = new Set<string>();
  const officialConfirmedOperators = new Set<string>();
  let demoRecords = 0;
  records.forEach((record) => {
    const operator =
      record.confirmedOperator && hasOperatorName(record.operatorName) ? record.operatorName.trim() : null;
    const recordPublishers = (record.publishers || []).map((name) => name.trim()).filter(Boolean);
    if (operator) {
      confirmedOperators.add(operator);
    }
    recordPublishers.forEach((name) => publishers.add(name));
    if (record.demo) {
      demoRecords++;
    } else {
      if (operator) {
        officialConfirmedOperators.add(operator);
      }
      recordPublishers.forEach((name) => officialPublishers.add(name));
    }
    let terc = normalizeTerc(record.terc);
    if (!terc || !coverage.has(terc)) {
      terc = isCoordinate(record.lat) && isCoordinate(record.lon) ? locate(index, record.lat, record.lon) : null;
    }
    if (terc) {
      if (record.demo) {
        coverage.get(terc).demoCount++;
      } else {
        coverage.get(terc).officialCount++;
      }
      recordPublishers.forEach((name) => publishersByGmina.get(terc).add(name));
      if (operator) {
        operatorsByGmina.get(terc).add(operator);
      }
    }
  });

  osmPoints.forEach((point) => {
    const terc = isCoordinate(point.lat) && isCoordinate(point.lon) ? locate(index, point.lat, point.lon) : null;
    if (terc) {
      coverage.get(terc).osmCount++;
    }
  });

  let gminyCovered = 0;
  let gminyDemoOnly = 0;
  let gaps = 0;
  coverage.forEach((gmina) => {
    gmina.publishers = Array.from(publishersByGmina.get(gmina.terc)).sort((a, b) => a.localeCompare(b, 'pl'));
    gmina.operators = Array.from(operatorsByGmina.get(gmina.terc)).sort((a, b) => a.localeCompare(b, 'pl'));
    if (gmina.officialCount > 0) {
      gmina.status = 'published';
      gminyCovered++;
    } else if (gmina.osmCount > 0) {
      // Demo records do not fill a gap in official data.
      gmina.status = 'gap';
      gaps++;
    } else if (gmina.demoCount > 0) {
      gmina.status = 'demo';
    }
    if (gmina.officialCount === 0 && gmina.demoCount > 0) {
      gminyDemoOnly++;
    }
  });

  return {
    records: records.length,
    publishers: publishers.size,
    confirmedOperators: confirmedOperators.size,
    demoRecords,
    demoPublishers: Array.from(publishers).filter((name) => !officialPublishers.has(name)).length,
    demoConfirmedOperators: Array.from(confirmedOperators).filter((name) => !officialConfirmedOperators.has(name))
      .length,
    gminyCovered,
    gminyDemoOnly,
    gminyTotal: gminy.length,
    gaps,
    gminy: coverage,
  };
}
