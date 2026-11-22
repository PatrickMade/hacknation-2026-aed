"""Source data (live from api.dane.gov.pl, committed snapshot as fallback) and its mapping to the AED profile
(aed-standard/mappings.csv). APP-46 2026-11-21, live refresh / PRG / operator rule APP-57 2026-11-22."""
import csv
import datetime
import gzip
import hashlib
import io
import json
import re
import urllib.request
import uuid
from pathlib import Path

from mcod.aed_aggregate import standard

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'aed' / 'sources'
PRG_FILE = Path(__file__).resolve().parents[2] / 'data' / 'aed' / 'prg' / 'gminy_dysponentow.geojson'
API_URL = 'https://api.dane.gov.pl/1.4'
HTTP_TIMEOUT = 20
AED_NAMESPACE = uuid.UUID('4f3b2a7e-6d1c-5b8a-9e0f-aed000000001')
CC0_URL = 'https://creativecommons.org/publicdomain/zero/1.0/'
CC_BY_URL = 'https://creativecommons.org/licenses/by/4.0/'
ODBL_URL = 'https://opendatacommons.org/licenses/odbl/1-0/'
LICENCES = {'CC0 1.0': CC0_URL, 'CC BY 4.0': CC_BY_URL}
OSM_ATTRIBUTION = '© OpenStreetMap contributors'
UNCONFIRMED = standard.SCHEMA['x-operatorUnconfirmed']  # placeholder, flag, forbiddenSourcePrefix
FROM_LOCATION = 'operator_from_location'
OPERATOR_NOTE = {
    'location': 'instytucja z opisu lokalizacji w źródle ({column}); nie jest potwierdzeniem dysponenta',
    'publisher': 'źródło nie nazywa instytucji w opisie lokalizacji: wydawca danych (publisher_name); nie jest '
                 'potwierdzeniem dysponenta',
}
UTC_STAMP = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z')

# terc: the dysponent's gmina in PRG (GUGiK ULDK, data/aed/prg/); a record is placed only inside it.
SOURCES = (
    {'slug': 'krosno', 'dataset_id': 3624, 'resource_id': 54632, 'file': 'Defibrylator_jAmxQcp.csv',
     'reader': 'krosno_marki', 'terc': '1861011'},
    {'slug': 'marki', 'dataset_id': 4955, 'resource_id': 68353, 'file': 'Defibrylator_GminaMiastoMarki_1.csv',
     'reader': 'marki', 'terc': '1434021'},
    {'slug': 'przemysl', 'dataset_id': 4581, 'resource_id': 62093, 'file': '1730818801_b50R6UVxPgoVdBbq.geojson',
     'reader': 'przemysl', 'terc': '1862011'},
    {'slug': 'warszawa', 'dataset_id': 39512, 'resource_id': 2512040, 'file': None,
     'reader': None, 'terc': None},
    {'slug': 'legionowo', 'dataset_id': 40593, 'resource_id': 2625221, 'file': 'aed.csv',
     'reader': 'legionowo', 'terc': '1408011'},
)
OSM_FILE = DATA_DIR / 'osm' / 'PL.geojson.gz'
OSM_SOURCE_URL = 'https://openaedmap.org/api/v1/countries/PL.geojson'


def retrieved_at():
    """Retrieval time of the committed snapshot."""
    return (DATA_DIR / 'retrieved_at.txt').read_text().strip()


def now_utc():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def load_json(slug, name):
    return json.loads((DATA_DIR / slug / name).read_text(encoding='utf-8'))


def http_get(url):
    """Read-only GET of a public URL; any error propagates to the caller, which falls back to the snapshot."""
    request = urllib.request.Request(url, headers={'User-Agent': 'aed-aggregator/1.0', 'Accept': '*/*'})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return response.read()


def meta_from(dataset_doc, resources_doc, institution_doc, source):
    resources = {int(r['id']): r['attributes'] for r in resources_doc['data']}
    return {'dataset': dataset_doc['data']['attributes'], 'resource': resources[source['resource_id']],
            'institution': institution_doc['data']['attributes']}


def snapshot(source, reason=None):
    meta = meta_from(load_json(source['slug'], 'dataset.json'), load_json(source['slug'], 'resources.json'),
                     load_json(source['slug'], 'institution.json'), source)
    content = (DATA_DIR / source['slug'] / source['file']).read_bytes() if source['file'] else None
    return {'source': source, 'meta': meta, 'content': content, 'origin': 'snapshot',
            'retrieved_at': retrieved_at(), 'reason': reason}


def live(source):
    """The source as published now: dataset, resources, institution and the data file, read-only."""
    dataset_doc = json.loads(http_get('{}/datasets/{}'.format(API_URL, source['dataset_id'])))
    resources_doc = json.loads(http_get('{}/datasets/{}/resources?per_page=100'.format(API_URL, source['dataset_id'])))
    institution_id = dataset_doc['data']['relationships']['institution']['data']['id']
    institution_doc = json.loads(http_get('{}/institutions/{}'.format(API_URL, institution_id)))
    meta = meta_from(dataset_doc, resources_doc, institution_doc, source)
    content = None
    if source['file']:
        content = http_get(meta['resource']['file_url'])
        content.decode('utf-8')  # an undecodable file is not used
        if not content.strip():
            raise ValueError('pusty plik zasobu')
    return {'source': source, 'meta': meta, 'content': content, 'origin': 'live', 'retrieved_at': now_utc(),
            'reason': None}


def load_source(source, use_live=True):
    if not use_live:
        return snapshot(source)
    try:
        return live(source)
    except Exception as error:  # network, HTTP, JSON or missing resource: the dated snapshot is used instead
        return snapshot(source, reason='{}: {}'.format(type(error).__name__, error)[:200])


def load_sources(use_live=True):
    return [load_source(source, use_live) for source in SOURCES]


def aed_id(source_key):
    return str(uuid.uuid5(AED_NAMESPACE, source_key))


def number(text):
    text = (text or '').strip().replace(',', '.')
    try:
        return round(float(text), 7)
    except ValueError:
        return None


def _prg():
    document = json.loads(PRG_FILE.read_text(encoding='utf-8'))
    return {f['properties']['terc']: f['geometry'] for f in document['features']}, document['properties']


GMINY, PRG_META = _prg()


def _in_ring(lon, lat, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def in_gmina(terc, lat, lon):
    """Point-in-polygon against the exact PRG boundary (outer rings minus holes)."""
    if lat is None or lon is None:
        return False
    return any(_in_ring(lon, lat, polygon[0]) and not any(_in_ring(lon, lat, hole) for hole in polygon[1:])
               for polygon in GMINY[terc]['coordinates'])


def place(record, terc, lat, lon, provenance):
    """Set coordinates only inside the dysponent's gmina (PRG); axis swap per record, with a flag."""
    prg = 'PRG (GUGiK ULDK, pobrano {})'.format(PRG_META['retrieved_at'][:10])
    if in_gmina(terc, lat, lon):
        record['latitude'], record['longitude'] = lat, lon
    elif in_gmina(terc, lon, lat):
        record['latitude'], record['longitude'] = lon, lat
        record['coordinate_method'] = 'unknown'  # not a confirmed source coordinate until the provider confirms
        record['quality_flags'].append('suspected_axis_swap')
        provenance['latitude'] = ('z kolumny opisanej jako długość geograficzna; osie zamienione, bo tylko tak punkt '
                                  'leży w granicach gminy dysponenta wg {}; do potwierdzenia przez dysponenta'.format(prg))
        provenance['longitude'] = ('z kolumny opisanej jako szerokość geograficzna; osie zamienione, bo tylko tak punkt '
                                   'leży w granicach gminy dysponenta wg {}; do potwierdzenia przez dysponenta'.format(prg))
    else:
        record['quality_flags'].append('outside_expected_area')
        provenance['latitude'] = provenance['longitude'] = (
            'współrzędne źródła leżą poza granicami gminy dysponenta wg {}; nie publikowane, oryginał w '
            'original_values'.format(prg))
        return
    record['terc'] = terc
    provenance['terc'] = 'gmina dysponenta; punkt w jej granicach wg {}'.format(prg)


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


def base_record(name, retrieved, updated, operator=None):
    """operator=None: the dysponent is not confirmed - placeholder plus flag (aed-standard x-operatorUnconfirmed)."""
    return {
        'name': name, 'location_kind': 'unknown', 'coordinate_method': 'source', 'country_code': 'PL',
        'indoor': 'unknown', 'access': 'unknown', 'locked': 'unknown', 'operational_status': 'unknown',
        'operator_name': operator or UNCONFIRMED['placeholder'], 'verification_method': 'unknown',
        'retrieved_at': retrieved, 'updated_at': updated, 'quality_flags': [UNCONFIRMED['flag']],
    }


def operator_from_source(record, loaded, provenance, institution=None, column=None):
    """Municipal sources name no dysponent: operator_name is the institution in the location text (or the
    publishing office when there is none), marked operator_from_location; never invented beyond the source text."""
    record['operator_name'] = institution or loaded['meta']['institution']['title']
    record['quality_flags'] = [flag for flag in record['quality_flags'] if flag != UNCONFIRMED['flag']]
    record['quality_flags'].append(FROM_LOCATION)
    provenance['operator_name'] = (OPERATOR_NOTE['location'].format(column=column) if institution
                                   else OPERATOR_NOTE['publisher'])


def origin_note(loaded):
    if loaded['origin'] == 'live':
        return 'pobrano z api.dane.gov.pl {}'.format(loaded['retrieved_at'])
    return 'kopia z {} (api.dane.gov.pl niedostępne: {})'.format(
        loaded['retrieved_at'], loaded['reason']) if loaded['reason'] else 'kopia z {}'.format(loaded['retrieved_at'])


def source_record(loaded, record_key, original, provenance):
    source, meta = loaded['source'], loaded['meta']
    licence = LICENCES[meta['dataset'].get('license_name')]  # unknown licence: KeyError, nothing is published
    entry = {
        'source_id': 'dane:dataset:{}'.format(source['dataset_id']),
        'source_record_id': record_key,
        'source_url': meta['resource']['file_url'],
        'retrieved_at': loaded['retrieved_at'],
        'license_url': licence,
        'source_version': 'resource:{}'.format(source['resource_id']),
        'source_data_date': meta['resource']['data_date'],
        'publisher_name': meta['institution']['title'],
        'original_values': original,
        'field_provenance': provenance,
    }
    if UTC_STAMP.fullmatch(meta['resource'].get('modified') or ''):
        entry['source_updated_at'] = meta['resource']['modified']
    if licence == CC_BY_URL:
        entry['attribution'] = '{}, dane.gov.pl zbiór {}'.format(meta['institution']['title'], source['dataset_id'])
    return entry


def updated_at(loaded):
    """The record changes when its source file changes, not on every daily fetch."""
    modified = loaded['meta']['resource'].get('modified') or ''
    return modified if UTC_STAMP.fullmatch(modified) else loaded['retrieved_at']


def finish(loaded, record, record_key, original, provenance):
    provenance.setdefault('source_records', origin_note(loaded))
    record['source_records'] = [source_record(loaded, record_key, original, provenance)]
    record['aed_id'] = aed_id('{}:{}'.format(record['source_records'][0]['source_id'], record_key))
    return record


def read_krosno_marki(loaded, rows, extra_flags=()):
    records = []
    for row in rows:
        row = {key.strip(): (value or '').strip() for key, value in row.items()}
        original = {key: row[key] for key in ('Długość geograficzna', 'Szerokość geograficzna', 'Nazwa',
                                             'Lokalizacja', 'Adres', 'Numer Id')}
        provenance = {'name': 'Lokalizacja (Nazwa zawiera tylko "Defibrylator")' if row['Lokalizacja'] else 'Nazwa'}
        record = base_record(row['Lokalizacja'] or row['Nazwa'], loaded['retrieved_at'], updated_at(loaded))
        record['quality_flags'].extend(extra_flags)
        operator_from_source(record, loaded, provenance, row['Lokalizacja'] or None, 'Lokalizacja')
        place(record, loaded['source']['terc'], number(row['Szerokość geograficzna']),
              number(row['Długość geograficzna']), provenance)
        address = split_address(row['Adres'])
        if address:
            record.update({key: value for key, value in address.items() if value})
            provenance['street'] = 'wydzielone z kolumny Adres'
        records.append(finish(loaded, record, row['Numer Id'], original, provenance))
    return records


def read_marki(loaded, raw):
    """Marki: one outer CSV column holding the inner CSV record (encoded_csv)."""
    outer = [row[0] for row in csv.reader(io.StringIO(raw)) if row]
    inner = list(csv.DictReader(io.StringIO('\n'.join(outer)), skipinitialspace=True))
    return read_krosno_marki(loaded, inner, extra_flags=('encoded_csv',))


def read_przemysl(loaded, raw):
    records = []
    for feature in json.loads(raw)['features']:
        props = feature['properties']
        lon, lat = feature['geometry']['coordinates'][:2]
        original = {key: props.get(key) for key in ('id', 'name', 'city', 'street', 'home_number', 'postcode')}
        original['geometry.coordinates'] = [lon, lat]
        provenance = {}
        record = base_record(props['name'], loaded['retrieved_at'], updated_at(loaded))
        operator_from_source(record, loaded, provenance)  # only a device label, no institution field
        place(record, loaded['source']['terc'], number(str(lat)), number(str(lon)), provenance)
        for field, key in (('locality', 'city'), ('street', 'street'), ('house_number', 'home_number')):
            if (props.get(key) or '').strip():
                record[field] = props[key].strip()
        if re.fullmatch(r'\d{2}-\d{3}', props.get('postcode') or ''):
            record['postcode'] = props['postcode']
        records.append(finish(loaded, record, str(props['id']), original, provenance))
    return records


def read_legionowo(loaded, raw):
    records = []
    for row in csv.DictReader(io.StringIO(raw.lstrip('\ufeff'))):
        row = {key: (value or '').strip() for key, value in row.items()}
        key = 'lokalny:' + hashlib.sha1(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
        provenance = {'source_record_id': 'brak ID w źródle; klucz lokalny z treści wiersza do czasu nadania ID przez dysponenta'}
        record = base_record(row['nazwa'], loaded['retrieved_at'], updated_at(loaded))
        operator_from_source(record, loaded, provenance, row['nazwa'] or None, 'nazwa')
        place(record, loaded['source']['terc'], number(row['szerokosc_geograficzna']),
              number(row['dlugosc_geograficzna']), provenance)
        for field, column in (('street_type', 'cecha_ulicy'), ('street', 'nazwa_ulicy'), ('house_number', 'nr_budynku'),
                              ('unit_number', 'nr_lokalu'), ('postcode', 'kod_pocztowy'), ('locality', 'miejscowosc')):
            if row[column]:
                record[field] = row[column]
        if re.fullmatch(r'\d{7}', row['kod_simc']):
            record['simc'] = row['kod_simc']
        if 'terc' in record:
            if row['kod_terc'] and not record['terc'].startswith(row['kod_terc']):
                record['quality_flags'].append('conflicting_sources')
            provenance['terc'] += '; kod_terc w źródle: {}'.format(row['kod_terc'] or 'brak')
        elif re.fullmatch(r'\d{7}', row['kod_terc']):
            record['terc'] = row['kod_terc']
        elif row['kod_terc']:
            record['quality_flags'].append('teryt_incomplete')
            provenance['terc'] = 'kod_terc ma {} cyfr; nie uzupełniany bez datowanego rejestru TERYT'.format(len(row['kod_terc']))
        records.append(finish(loaded, record, key, row, provenance))
    return records


READERS = {'krosno_marki': lambda loaded, raw: read_krosno_marki(loaded, csv.DictReader(io.StringIO(raw))),
           'marki': read_marki, 'przemysl': read_przemysl, 'legionowo': read_legionowo}


def official_records(loaded=None):
    """All municipal records mapped to the profile, before deduplication. loaded: load_sources() result; by
    default the committed snapshots (deterministic, offline)."""
    loaded = loaded if loaded is not None else load_sources(use_live=False)
    records = []
    for index, item in enumerate(loaded):
        if not item['source']['reader'] or item['content'] is None:
            continue
        try:
            records.extend(READERS[item['source']['reader']](item, item['content'].decode('utf-8')))
        except Exception as error:  # a live file in a changed layout: use the dated snapshot for this source
            if item['origin'] != 'live':
                raise
            fallback = snapshot(item['source'], reason='plik w zmienionym układzie: {}: {}'.format(
                type(error).__name__, error)[:200])
            loaded[index] = fallback  # publish_sources then republishes the snapshot file as well
            records.extend(READERS[item['source']['reader']](fallback, fallback['content'].decode('utf-8')))
    return records


PUBLISHED_TAG = 'zgodny ze standardem AED'


def published_records():
    """Records of the newest published CSV resource of each dataset tagged PUBLISHED_TAG (e.g. by the provider
    wizard, APP-43). Each publication is a full snapshot, so older CSV resources of the same dataset are ignored;
    resources in other formats (a PDF, a link) neither count nor hide the CSV.

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
        main = resource.files.filter(is_main=True).first()
        if main is None or not (main.file.name or '').lower().endswith('.csv'):
            continue
        seen_datasets.add(resource.dataset_id)
        try:
            with main.file.open('rb') as handle:
                content = handle.read()
        except (ValueError, OSError):  # missing media file
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
    # The operator tag is only a candidate: every OSM record keeps operator_unconfirmed.
    record = base_record(without_contacts(props.get('name')) or 'Defibrylator AED', retrieved, retrieved, operator)
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
