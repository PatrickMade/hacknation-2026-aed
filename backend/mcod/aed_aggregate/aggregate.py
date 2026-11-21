"""Deduplication, per-record validation and serialisation of the AED report."""
import json
import math
import re
import unicodedata

from mcod.aed_aggregate import standard
from mcod.aed_aggregate.sources import aed_id

MERGE_DISTANCE_M = 25.0


def distance_m(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a['latitude'], a['longitude'], b['latitude'], b['longitude']))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def normalise(text):
    text = unicodedata.normalize('NFKD', (text or '').lower())
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def place_key(record):
    return (normalise(record.get('name')), normalise(record.get('street')), normalise(record.get('house_number')))


def source_keys(record):
    return {(s['source_id'], s['source_record_id']) for s in record['source_records']}


def add_flag(record, flag):
    if flag not in record['quality_flags']:
        record['quality_flags'].append(flag)


def merge(target, other):
    """Fold `other` into `target`: union of provenance, conflicting values flagged, never overwritten."""
    known = source_keys(target)
    target['source_records'].extend(s for s in other['source_records']
                                    if (s['source_id'], s['source_record_id']) not in known)
    for flag in other['quality_flags']:
        add_flag(target, flag)
    for field in standard.FIELDS:
        if field in ('aed_id', 'source_records', 'quality_flags', 'retrieved_at', 'updated_at'):
            continue
        mine, theirs = target.get(field), other.get(field)
        if mine in (None, '', 'unknown') and theirs not in (None, '', 'unknown'):
            target[field] = theirs
        elif theirs not in (None, '', 'unknown') and mine != theirs and field not in ('latitude', 'longitude'):
            add_flag(target, 'conflicting_sources')
    target['retrieved_at'] = max(target['retrieved_at'], other['retrieved_at'])
    target['updated_at'] = max(target['updated_at'], other['updated_at'])


def deduplicate(records):
    """Same source identity merges; under 25 m merges only with the same name and address, else duplicate_candidate."""
    result = []
    by_key = {}
    for record in records:
        record = json.loads(json.dumps(record))  # never mutate the caller's records
        match = next((by_key[key] for key in source_keys(record) if key in by_key), None)
        if match is None and record.get('latitude') is not None:
            for kept in result:
                if kept.get('latitude') is None or distance_m(kept, record) >= MERGE_DISTANCE_M:
                    continue
                if place_key(kept) == place_key(record):
                    match = kept
                    break
                add_flag(kept, 'duplicate_candidate')
                add_flag(record, 'duplicate_candidate')
        if match is None:
            result.append(record)
            match = record
        else:
            merge(match, record)
        for key in source_keys(record):
            by_key[key] = match
    for record in result:
        # Stable identity: UUIDv5 of the smallest namespaced source key, whatever the input order.
        first = min(source_keys(record))
        record['aed_id'] = aed_id('{}:{}'.format(*first))
        record['quality_flags'].sort()
    return sorted(result, key=lambda r: r['aed_id'])


def check(records):
    """Split into records that pass validate.py's rules and rejected ones with their reasons."""
    accepted, rejected = [], []
    for record in records:
        errors = standard.record_errors(record)
        (rejected if errors else accepted).append((record, errors))
    return [r for r, _ in accepted], rejected


def to_geojson(records):
    features = []
    for record in records:
        if record.get('latitude') is None:
            continue
        properties = {name: record[name] for name in standard.FIELDS
                      if name not in ('latitude', 'longitude') and record.get(name) not in (None, '')}
        features.append({'type': 'Feature', 'properties': properties,
                         'geometry': {'type': 'Point', 'coordinates': [record['longitude'], record['latitude']]}})
    return json.dumps({'type': 'FeatureCollection', 'features': features}, ensure_ascii=False, indent=1).encode('utf-8')
