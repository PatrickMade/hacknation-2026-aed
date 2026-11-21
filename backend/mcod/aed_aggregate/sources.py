"""Source snapshots and their mapping to the AED profile (aed-standard/mappings.csv), 2026-11-21."""
import csv
import gzip
import hashlib
import io
import json
import re
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'aed' / 'sources'
AED_NAMESPACE = uuid.UUID('4f3b2a7e-6d1c-5b8a-9e0f-aed000000001')
CC0_URL = 'https://creativecommons.org/publicdomain/zero/1.0/'
CC_BY_URL = 'https://creativecommons.org/licenses/by/4.0/'
ODBL_URL = 'https://opendatacommons.org/licenses/odbl/1-0/'
LICENCES = {'CC0 1.0': CC0_URL, 'CC BY 4.0': CC_BY_URL}
OSM_ATTRIBUTION = '© OpenStreetMap contributors'
OPERATOR_NOTE = 'wydawca zbioru źródłowego w dane.gov.pl; dysponent do potwierdzenia'

# Expected area of each municipal source (WGS84 bounding box with a margin),
# used to decide a per-record axis swap or to withhold implausible coordinates.
SOURCES = (
    {'slug': 'krosno', 'dataset_id': 3624, 'resource_id': 54632, 'file': 'Defibrylator_jAmxQcp.csv',
     'reader': 'krosno_marki', 'area': (49.64, 49.76, 21.68, 21.84)},
    {'slug': 'marki', 'dataset_id': 4955, 'resource_id': 68353, 'file': 'Defibrylator_GminaMiastoMarki_1.csv',
     'reader': 'marki', 'area': (52.29, 52.37, 21.05, 21.17)},
    {'slug': 'przemysl', 'dataset_id': 4581, 'resource_id': 62093, 'file': '1730818801_b50R6UVxPgoVdBbq.geojson',
     'reader': 'przemysl', 'area': (49.73, 49.84, 22.68, 22.87)},
    {'slug': 'warszawa', 'dataset_id': 39512, 'resource_id': 2512040, 'file': None,
     'reader': None, 'area': None},
    {'slug': 'legionowo', 'dataset_id': 40593, 'resource_id': 2625221, 'file': 'aed.csv',
     'reader': 'legionowo', 'area': (52.37, 52.44, 20.87, 20.99)},
)
OSM_FILE = DATA_DIR / 'osm' / 'PL.geojson.gz'
OSM_SOURCE_URL = 'https://openaedmap.org/api/v1/countries/PL.geojson'


def retrieved_at():
    return (DATA_DIR / 'retrieved_at.txt').read_text().strip()


def load_json(slug, name):
    return json.loads((DATA_DIR / slug / name).read_text(encoding='utf-8'))


def source_meta(source):
    """Original dane.gov.pl metadata of the snapshot: dataset, chosen resource, institution."""
    dataset = load_json(source['slug'], 'dataset.json')['data']['attributes']
    resources = {int(r['id']): r['attributes'] for r in load_json(source['slug'], 'resources.json')['data']}
    institution = load_json(source['slug'], 'institution.json')['data']['attributes']
    return {'dataset': dataset, 'resource': resources[source['resource_id']], 'institution': institution}


def aed_id(source_key):
    return str(uuid.uuid5(AED_NAMESPACE, source_key))


def number(text):
    text = (text or '').strip().replace(',', '.')
    try:
        return round(float(text), 7)
    except ValueError:
        return None


def in_area(area, lat, lon):
    return lat is not None and lon is not None and area[0] <= lat <= area[1] and area[2] <= lon <= area[3]


def place(record, area, lat, lon, provenance):
    """Set coordinates only when they fall in the source's expected area; axis swap per record, with a flag."""
    if in_area(area, lat, lon):
        record['latitude'], record['longitude'] = lat, lon
    elif in_area(area, lon, lat):
        record['latitude'], record['longitude'] = lon, lat
        record['coordinate_method'] = 'unknown'  # not a confirmed source coordinate until the provider confirms
        record['quality_flags'].append('suspected_axis_swap')
        provenance['latitude'] = 'z kolumny opisanej jako długość geograficzna; osie zamienione, bo tylko tak punkt leży w obszarze gminy (prostokąt); do potwierdzenia przez dysponenta'
        provenance['longitude'] = 'z kolumny opisanej jako szerokość geograficzna; osie zamienione, bo tylko tak punkt leży w obszarze gminy (prostokąt); do potwierdzenia przez dysponenta'
    else:
        record['quality_flags'].append('outside_expected_area')
        provenance['latitude'] = provenance['longitude'] = (
            'współrzędne źródła leżą poza obszarem gminy dysponenta (prostokąt); nie publikowane, oryginał w original_values')


ADDRESS = re.compile(
    r'^(?:(?P<type>ul\.|al\.+|pl\.|os\.)\s*)?(?P<street>[^,]*?[^\s,\d][^,]*?)(?:\s+(?P<number>\d+[A-Za-z]?(?:/\d+[A-Za-z]?)?))?'
    r',\s*(?P<postcode>\d{2}-\d{3})\s+(?P<locality>[^,]+)$',
    re.IGNORECASE,
)
STREET_TYPES = {'ul.': 'ulica', 'al.': 'aleja', 'pl.': 'plac', 'os.': 'osiedle'}


def split_address(text):
    """Conservative split of 'ul. Jasna 5, 38-400 Krosno'; None when the text does not match exactly."""
    match = ADDRESS.match(' '.join((text or '').split()))
    if not match:
        return None
    kind = (match.group('type') or '').lower()
    kind = re.sub(r'\.+$', '.', kind)
    return {
        'street_type': STREET_TYPES.get(kind),
        'street': match.group('street').strip(),
        'house_number': match.group('number'),
        'postcode': match.group('postcode'),
        'locality': match.group('locality').strip(),
    }


def base_record(name, operator, retrieved):
    return {
        'name': name, 'location_kind': 'unknown', 'coordinate_method': 'source', 'country_code': 'PL',
        'indoor': 'unknown', 'access': 'unknown', 'locked': 'unknown', 'operational_status': 'unknown',
        'operator_name': operator, 'verification_method': 'unknown',
        'retrieved_at': retrieved, 'updated_at': retrieved, 'quality_flags': [],
    }


def source_record(source, meta, record_key, original, provenance, retrieved):
    licence = LICENCES[meta['dataset'].get('license_name')]  # unknown licence: KeyError, nothing is published
    entry = {
        'source_id': 'dane:dataset:{}'.format(source['dataset_id']),
        'source_record_id': record_key,
        'source_url': meta['resource']['file_url'],
        'retrieved_at': retrieved,
        'license_url': licence,
        'source_version': 'resource:{}'.format(source['resource_id']),
        'source_data_date': meta['resource']['data_date'],
        'original_values': original,
        'field_provenance': provenance,
    }
    if licence == CC_BY_URL:
        entry['attribution'] = '{}, dane.gov.pl zbiór {}'.format(meta['institution']['title'], source['dataset_id'])
    return entry


def finish(source, meta, record, record_key, original, provenance, retrieved):
    provenance.setdefault('operator_name', OPERATOR_NOTE)
    record['source_records'] = [source_record(source, meta, record_key, original, provenance, retrieved)]
    record['aed_id'] = aed_id('{}:{}'.format(record['source_records'][0]['source_id'], record_key))
    return record


def read_krosno_marki(source, meta, rows, retrieved, extra_flags=()):
    records = []
    for row in rows:
        row = {key.strip(): (value or '').strip() for key, value in row.items()}
        original = {key: row[key] for key in ('Długość geograficzna', 'Szerokość geograficzna', 'Nazwa',
                                             'Lokalizacja', 'Adres', 'Numer Id')}
        provenance = {'name': 'Lokalizacja (Nazwa zawiera tylko "Defibrylator")' if row['Lokalizacja'] else 'Nazwa'}
        record = base_record(row['Lokalizacja'] or row['Nazwa'], meta['institution']['title'], retrieved)
        record['quality_flags'].extend(extra_flags)
        place(record, source['area'], number(row['Szerokość geograficzna']), number(row['Długość geograficzna']),
              provenance)
        address = split_address(row['Adres'])
        if address:
            record.update({key: value for key, value in address.items() if value})
            provenance['street'] = 'wydzielone z kolumny Adres'
        records.append(finish(source, meta, record, row['Numer Id'], original, provenance, retrieved))
    return records


def read_marki(source, meta, raw, retrieved):
    """Marki: one outer CSV column holding the inner CSV record (encoded_csv)."""
    outer = [row[0] for row in csv.reader(io.StringIO(raw)) if row]
    inner = list(csv.DictReader(io.StringIO('\n'.join(outer)), skipinitialspace=True))
    return read_krosno_marki(source, meta, inner, retrieved, extra_flags=('encoded_csv',))


def read_przemysl(source, meta, raw, retrieved):
    records = []
    for feature in json.loads(raw)['features']:
        props = feature['properties']
        lon, lat = feature['geometry']['coordinates'][:2]
        original = {key: props.get(key) for key in ('id', 'name', 'city', 'street', 'home_number', 'postcode')}
        original['geometry.coordinates'] = [lon, lat]
        provenance = {}
        record = base_record(props['name'], meta['institution']['title'], retrieved)
        place(record, source['area'], number(str(lat)), number(str(lon)), provenance)
        for field, key in (('locality', 'city'), ('street', 'street'), ('house_number', 'home_number')):
            if (props.get(key) or '').strip():
                record[field] = props[key].strip()
        if re.fullmatch(r'\d{2}-\d{3}', props.get('postcode') or ''):
            record['postcode'] = props['postcode']
        records.append(finish(source, meta, record, str(props['id']), original, provenance, retrieved))
    return records


def read_legionowo(source, meta, raw, retrieved):
    records = []
    for row in csv.DictReader(io.StringIO(raw.lstrip('﻿'))):
        row = {key: (value or '').strip() for key, value in row.items()}
        key = 'lokalny:' + hashlib.sha1(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
        provenance = {'source_record_id': 'brak ID w źródle; klucz lokalny z treści wiersza do czasu nadania ID przez dysponenta'}
        record = base_record(row['nazwa'], meta['institution']['title'], retrieved)
        place(record, source['area'], number(row['szerokosc_geograficzna']), number(row['dlugosc_geograficzna']),
              provenance)
        for field, column in (('street_type', 'cecha_ulicy'), ('street', 'nazwa_ulicy'), ('house_number', 'nr_budynku'),
                              ('unit_number', 'nr_lokalu'), ('postcode', 'kod_pocztowy'), ('locality', 'miejscowosc')):
            if row[column]:
                record[field] = row[column]
        if re.fullmatch(r'\d{7}', row['kod_simc']):
            record['simc'] = row['kod_simc']
        if re.fullmatch(r'\d{7}', row['kod_terc']):
            record['terc'] = row['kod_terc']
        elif row['kod_terc']:
            record['quality_flags'].append('teryt_incomplete')
            provenance['terc'] = 'kod_terc ma {} cyfr; nie uzupełniany bez datowanego rejestru TERYT'.format(len(row['kod_terc']))
        records.append(finish(source, meta, record, key, row, provenance, retrieved))
    return records


READERS = {'krosno_marki': lambda s, m, raw, r: read_krosno_marki(s, m, csv.DictReader(io.StringIO(raw)), r),
           'marki': read_marki, 'przemysl': read_przemysl, 'legionowo': read_legionowo}


def official_records():
    """All municipal records mapped to the profile, before deduplication."""
    retrieved = retrieved_at()
    records = []
    for source in SOURCES:
        if not source['reader']:
            continue
        raw = (DATA_DIR / source['slug'] / source['file']).read_text(encoding='utf-8')
        records.extend(READERS[source['reader']](source, source_meta(source), raw, retrieved))
    return records


PUBLISHED_TAG = 'zgodny ze standardem AED'


def published_records():
    """Records of the newest published CSV resource of each dataset tagged PUBLISHED_TAG (e.g. by the provider
    wizard, APP-43). Each publication is a full snapshot, so older resources of the same dataset are ignored.

    A file is used only when it passes validate.py as a whole and every record names the publishing institution
    as its source (`source_id` = `dysponent:<institution slug>`); its cells are parsed with the profile's own field
    rules. Returns (records, skipped resource ids) - unreadable or non-conforming files are skipped, not fatal.
    """
    import tempfile

    from mcod.aed_aggregate import standard
    from mcod.resources.models import Resource

    records, skipped, seen_datasets = [], [], set()
    resources = Resource.objects.filter(
        status='published', dataset__status='published', dataset__tags__name=PUBLISHED_TAG,
    ).select_related('dataset__organization').distinct().order_by('-pk')
    for resource in resources:
        if resource.dataset_id in seen_datasets:
            continue
        seen_datasets.add(resource.dataset_id)
        main = resource.files.filter(is_main=True).first()
        try:
            with main.file.open('rb') as handle:
                content = handle.read()
        except (AttributeError, ValueError, OSError):  # no main file, empty FileField, missing media file
            skipped.append(resource.pk)
            continue
        with tempfile.NamedTemporaryFile(suffix='.csv') as temp:
            temp.write(content)
            temp.flush()
            if standard.file_errors(temp.name):
                skipped.append(resource.pk)
                continue
        own_source = 'dysponent:' + resource.dataset.organization.slug
        rows = []
        for row in csv.DictReader(io.StringIO(content.decode('utf-8'), newline='')):
            record = {}
            for name, value in row.items():
                parsed = standard.validator.scalar(value, standard.FIELD_DEFS[name])
                if parsed is not None:
                    record[name] = parsed
            rows.append(record)
        if any(s['source_id'] != own_source for record in rows for s in record['source_records']):
            skipped.append(resource.pk)
            continue
        records.extend(rows)
    return records, skipped


PHONE_CANDIDATE = re.compile(r'\+?\d[\d\s().-]{7,}\d')
HOURS = re.compile(r'\d{1,2}[.:]\d{2}\s*-\s*\d{1,2}[.:]\d{2}')
EMAIL = re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+')


def has_phone(value):
    """9+ digits in one run, after removing opening hours; dates, coordinates and postcodes stay below that."""
    text = HOURS.sub(' ', value or '')
    for match in PHONE_CANDIDATE.finditer(text):
        if len(re.sub(r'\D', '', match.group())) >= 9 and not re.search(r'\d\.\d{4,}', match.group()):
            return True
    return False


def without_contacts(value):
    """OSM free text may carry phone numbers, e-mails or intercom codes: such a value is not published."""
    value = ' '.join((value or '').split())
    if not value or has_phone(value) or EMAIL.search(value) or re.search(r'domofon|kod\b', value, re.I):
        return None
    return value


OSM_ACCESS = {'yes': 'public', 'permissive': 'permissive', 'customers': 'customers', 'private': 'private', 'no': 'no'}


def osm_record(feature, retrieved):
    props = feature['properties']
    kind, ident = props['@osm_type'], props['@osm_id']
    lon, lat = feature['geometry']['coordinates'][:2]
    operator = without_contacts(props.get('operator'))
    if operator and not re.search(r'[^\W\d_]', operator):
        operator = None  # a bare number is not an operator name
    record = base_record(without_contacts(props.get('name')) or 'Defibrylator AED',
                         operator or 'nieustalony (OpenStreetMap)', retrieved)
    record['latitude'], record['longitude'] = number(str(lat)), number(str(lon))
    record['indoor'] = props.get('indoor') if props.get('indoor') in ('yes', 'no') else 'unknown'
    record['locked'] = props.get('locked') if props.get('locked') in ('yes', 'no') else 'unknown'
    record['access'] = OSM_ACCESS.get(props.get('access'), 'unknown')
    location = props.get('defibrillator:location:pl') or props.get('defibrillator:location')
    for field, value in (('location_description', location), ('level', props.get('level')),
                         ('level_ref', props.get('level:ref')), ('opening_hours_raw', props.get('opening_hours')),
                         ('locality', props.get('addr:city')), ('street', props.get('addr:street')),
                         ('house_number', props.get('addr:housenumber')), ('unit_number', props.get('addr:unit')),
                         ('manufacturer', props.get('manufacturer')), ('model', props.get('model'))):
        value = without_contacts(value)
        if value:
            record[field] = value
    if re.fullmatch(r'\d{2}-\d{3}', props.get('addr:postcode') or ''):
        record['postcode'] = props['addr:postcode']
    if re.fullmatch(r'\d{7}', props.get('addr:city:simc') or ''):
        record['simc'] = props['addr:city:simc']
    key = '{}/{}'.format(kind, ident)
    record['source_records'] = [{
        'source_id': 'osm', 'source_record_id': key, 'source_url': 'https://www.openstreetmap.org/' + key,
        'retrieved_at': retrieved, 'license_url': ODBL_URL, 'attribution': OSM_ATTRIBUTION,
        'source_version': str(props.get('@osm_version', '')),
        'field_provenance': {'operator_name': 'tag operator jako kandydat; dysponent niepotwierdzony',
                             'source_records': 'kopia OSM z eksportu OpenAEDMap ' + OSM_SOURCE_URL},
    }]
    record['aed_id'] = aed_id('osm:' + key)
    return record


def osm_records():
    retrieved = retrieved_at()
    with gzip.open(str(OSM_FILE), 'rt', encoding='utf-8') as handle:
        features = json.load(handle)['features']
    return [osm_record(feature, retrieved) for feature in features if feature['geometry']['type'] == 'Point']
