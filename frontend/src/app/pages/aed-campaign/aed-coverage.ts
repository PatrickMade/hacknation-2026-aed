/**
 * Coverage of Polish gminy by published AED data (pure functions, no Angular).
 */

export interface GminaFeature {
  type: 'Feature';
  properties: { terc: string; name: string };
  geometry: { type: 'Polygon'; coordinates: number[][][] } | { type: 'MultiPolygon'; coordinates: number[][][][] };
}

export interface AedOfficialRecord {
  terc: string | null;
  operatorName: string | null;
  /** Institutions that published the record (source_records[].publisher_name). */
  publishers: string[];
  lat: number | null;
  lon: number | null;
}

export interface AedPoint {
  lat: number;
  lon: number;
}

export type GminaStatus = 'published' | 'gap' | 'none';

export interface GminaCoverage {
  terc: string;
  name: string;
  status: GminaStatus;
  officialCount: number;
  /** Data publishers of the official records in the gmina. */
  publishers: string[];
  osmCount: number;
}

export interface CoverageSummary {
  records: number;
  /** Unique data publishers (source_records[].publisher_name). */
  publishers: number;
  /** Unique operator_name values that are confirmed, i.e. not empty and not "nieustalony". */
  confirmedOperators: number;
  gminyCovered: number;
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

/**
 * A confirmed dysponent has a real name. The raport zbiorczy marks records whose dysponent no source confirms
 * with "nieustalony" (and the operator_unconfirmed flag); OSM uses "nieustalony (OpenStreetMap)".
 */
export function isConfirmedOperator(name: string | null | undefined): boolean {
  const text = (name || '').trim();
  return text !== '' && !/^nieustalony/i.test(text);
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
  gminy.forEach((feature) => {
    coverage.set(feature.properties.terc, {
      terc: feature.properties.terc,
      name: feature.properties.name,
      status: 'none',
      officialCount: 0,
      publishers: [],
      osmCount: 0,
    });
    publishersByGmina.set(feature.properties.terc, new Set());
  });

  const publishers = new Set<string>();
  const confirmedOperators = new Set<string>();
  records.forEach((record) => {
    if (isConfirmedOperator(record.operatorName)) {
      confirmedOperators.add(record.operatorName.trim());
    }
    const recordPublishers = (record.publishers || []).map((name) => name.trim()).filter(Boolean);
    recordPublishers.forEach((name) => publishers.add(name));
    let terc = normalizeTerc(record.terc);
    if (!terc || !coverage.has(terc)) {
      terc = isCoordinate(record.lat) && isCoordinate(record.lon) ? locate(index, record.lat, record.lon) : null;
    }
    if (terc) {
      coverage.get(terc).officialCount++;
      recordPublishers.forEach((name) => publishersByGmina.get(terc).add(name));
    }
  });

  osmPoints.forEach((point) => {
    const terc = isCoordinate(point.lat) && isCoordinate(point.lon) ? locate(index, point.lat, point.lon) : null;
    if (terc) {
      coverage.get(terc).osmCount++;
    }
  });

  let gminyCovered = 0;
  let gaps = 0;
  coverage.forEach((gmina) => {
    gmina.publishers = Array.from(publishersByGmina.get(gmina.terc)).sort((a, b) => a.localeCompare(b, 'pl'));
    if (gmina.officialCount > 0) {
      gmina.status = 'published';
      gminyCovered++;
    } else if (gmina.osmCount > 0) {
      gmina.status = 'gap';
      gaps++;
    }
  });

  return {
    records: records.length,
    publishers: publishers.size,
    confirmedOperators: confirmedOperators.size,
    gminyCovered,
    gminyTotal: gminy.length,
    gaps,
    gminy: coverage,
  };
}
