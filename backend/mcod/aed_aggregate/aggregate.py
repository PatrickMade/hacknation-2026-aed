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


UNKNOWN_VALUES = (None, '', 'unknown', standard.SCHEMA['x-operatorUnconfirmed']['placeholder'])
DERIVED_OPERATOR_FLAGS = (standard.SCHEMA['x-operatorUnconfirmed']['flag'], 'operator_from_location')
OPERATOR_FIELDS = ('operator_name', 'operator_regon')


def merge(target, other):
    """Fold `other` into `target`: union of provenance, conflicting values flagged, never overwritten.
    A confirmed dysponent (a `dysponent:` source) supplies operator_name/operator_regon and clears the flags of a
    derived or unconfirmed operator."""
    provider = other if from_provider(other) else (target if from_provider(target) else None)
    known = source_keys(target)
    target['source_records'].extend(s for s in other['source_records']
                                    if (s['source_id'], s['source_record_id']) not in known)
    for flag in other['quality_flags']:
        add_flag(target, flag)
    for field in standard.FIELDS:
        if field in ('aed_id', 'source_records', 'quality_flags', 'retrieved_at', 'updated_at'):
            continue
        if provider is not None and field in OPERATOR_FIELDS:
            if provider is other and other.get(field) not in UNKNOWN_VALUES:
                target[field] = other[field]
            continue
        mine, theirs = target.get(field), other.get(field)
        if mine in UNKNOWN_VALUES and theirs not in UNKNOWN_VALUES:
            target[field] = theirs
            for source in other['source_records']:
                source.setdefault('field_provenance', {})[field] = 'wartość przyjęta z tego źródła: pierwsze niepuste'
        elif theirs not in UNKNOWN_VALUES and mine != theirs and field not in ('latitude', 'longitude'):
            add_flag(target, 'conflicting_sources')
    if provider is not None:
        target['quality_flags'] = [flag for flag in target['quality_flags'] if flag not in DERIVED_OPERATOR_FLAGS]
    target['retrieved_at'] = max(target['retrieved_at'], other['retrieved_at'])
    target['updated_at'] = max(target['updated_at'], other['updated_at'])


PROVIDER_PREFIX = 'dysponent:'


def from_provider(record):
    """A record published by its dysponent in the profile (e.g. through the wizard) carries their aed_id."""
    return any(s['source_id'].startswith(PROVIDER_PREFIX) for s in record['source_records'])


def deduplicate(records):
    """Same source identity merges; under 25 m merges only with the same name and address, else duplicate_candidate.

    aed_id: the dysponent's own id when a provider record is part of the result (aed-standard: assigned once by
    the dysponent and kept), else UUIDv5 of the smallest namespaced source key.
    """
    result = []
    by_key = {}
    provider_ids = {}
    for record in records:
        record = json.loads(json.dumps(record))  # never mutate the caller's records
        match = next((by_key[key] for key in source_keys(record) if key in by_key), None)
        if match is None and record.get('latitude') is not None:
            for kept in result:
                if kept.get('latitude') is None or distance_m(kept, record) >= MERGE_DISTANCE_M:
                    continue
                # Same place and name from ANOTHER source is one device; within one source it is two devices.
                other_source = not {s for s, _ in source_keys(kept)} & {s for s, _ in source_keys(record)}
                if other_source and place_key(kept) == place_key(record):
                    match = kept
                    break
                add_flag(kept, 'duplicate_candidate')
                add_flag(record, 'duplicate_candidate')
        if match is None:
            result.append(record)
            match = record
        else:
            merge(match, record)
        if from_provider(record) and record.get('aed_id'):
            provider_ids.setdefault(id(match), record['aed_id'])
        for key in source_keys(record):
            by_key[key] = match
    used = set()
    for record in result:
        # Stable identity: UUIDv5 of the smallest namespaced source key, whatever the input order. A provider id
        # is kept only while unique in the report (validate.py rejects repeated ids, case-insensitive).
        first = min(source_keys(record))
        provider = provider_ids.get(id(record))
        record['aed_id'] = provider if provider and provider.lower() not in used else aed_id('{}:{}'.format(*first))
        used.add(record['aed_id'].lower())
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
