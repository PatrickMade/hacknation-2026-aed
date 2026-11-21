"""Publish the source snapshots and the AED report as portal datasets and resources (idempotent by ext_ident)."""
import datetime
import hashlib
import logging

from django.core.files.base import ContentFile
from django.db import transaction

from mcod.aed_aggregate import sources, standard
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource, ResourceFile
from mcod.special_signs.models import SpecialSign
from mcod.tags.models import Tag

logger = logging.getLogger('mcod')

OPERATOR = {'slug': 'aed-operator-portalu', 'title': 'Ministerstwo Cyfryzacji - operator portalu (instancja lokalna)'}
REPORT_EXT = 'aed-raport-zbiorczy'
TAGS = ('AED', 'defibrylator', 'raport zbiorczy')
REPORT_NOTES = (
    'Raport zbiorczy AED: jeden zbiór rekordów o automatycznych defibrylatorach zewnętrznych (AED) z zasobów '
    'dysponentów opublikowanych w dane.gov.pl, sprowadzonych do wzorcowego zakresu danych AED (aed-standard), '
    'zwalidowanych i zdeduplikowanych. Każdy rekord wskazuje dysponenta (operator_name) i pochodzenie '
    '(source_records: zbiór, zasób, klucz rekordu, data pobrania, licencja). Flagi jakości (quality_flags) '
    'oznaczają m.in. zamienione osie współrzędnych, punkty poza gminą dysponenta, niepełny TERYT i kandydatów '
    'na duplikaty. Status działania, dostępność i godziny są "unknown", bo źródła ich nie potwierdzają. '
    'Wzór publikacji: raport zbiorczy DGA (dane.gov.pl, zbiór 4354). Instancja demonstracyjna HackNation 2026.'
)
REPORT_LICENCE_NOTE = (
    'Zasoby "Raport zbiorczy AED" (CSV, GeoJSON): CC BY 4.0, z zachowaniem warunków źródeł: Urząd Miasta Krosna, '
    'Urząd Miejski w Przemyślu, Urząd Miasta Legionowo (CC0 1.0), Urząd Miasta Marki (CC BY 4.0). '
    'Zasób "Punkty AED z OpenStreetMap - Polska" NIE jest objęty CC BY 4.0: obowiązuje ODbL 1.0 '
    '(https://opendatacommons.org/licenses/odbl/1-0/), © OpenStreetMap contributors.'
)


class RefreshError(Exception):
    pass


def bootstrap_user():
    from mcod.users.models import User
    user = User.objects.filter(email='superadmin@mcod.local', is_superuser=True).first()
    if user is None:
        raise RefreshError('Brak konta superadmin@mcod.local: najpierw uruchom seed_jury.')
    return user


def tags():
    return [Tag.objects.get_or_create(name=name, language='pl')[0] for name in TAGS]


def empty_cell_sign(user):
    """The portal's own way to declare a missing value: the AED profile leaves unknown values empty."""
    sign = SpecialSign.objects.filter(symbol='').first()
    if sign is None:
        sign = SpecialSign.objects.create(
            symbol='', name='brak danych', status='published', created_by=user, modified_by=user,
            description='Pusta komórka: wartość nieznana albo celowo niepublikowana (np. współrzędne poza gminą '
                        'dysponenta, zob. quality_flags). Zgodnie z wzorcowym zakresem danych AED.')
    return sign


def upsert_dataset(ext_ident, organization, user, **fields):
    dataset = Dataset.raw.filter(ext_ident=ext_ident).first()
    if dataset is None:
        dataset = Dataset(ext_ident=ext_ident, created_by=user)
    dataset.organization = organization
    dataset.modified_by = user
    dataset.status = 'published'
    dataset.is_removed = False
    for key, value in fields.items():
        setattr(dataset, key, value)
    dataset.save()
    dataset.tags.set(tags())
    return dataset


def upsert_resource(ext_ident, dataset, user, title, description, data_date, filename=None, content=None,
                    link=None, geo=False, process=True):
    """Create or update one resource; file content is replaced only when it changed."""
    resource = Resource.raw.filter(ext_ident=ext_ident).first()
    created = resource is None
    if created:
        # Draft first: a published resource would also queue the file pipeline on the worker.
        resource = Resource(ext_ident=ext_ident, created_by=user, status='draft')
    resource.dataset = dataset
    resource.title, resource.description = title, description
    resource.data_date = data_date
    resource.modified_by = user
    resource.is_removed = False
    if link:
        resource.link, resource.type = link, 'website'
        resource.status = 'published'
        resource.save()
        return resource
    resource.save()
    if geo:
        resource.special_signs.set([empty_cell_sign(user)])
    main = resource.files.filter(is_main=True).first()
    digest = hashlib.sha256(content).hexdigest()
    changed = main is None or _digest(main) != digest
    if main is None:
        main = ResourceFile(resource=resource, is_main=True)
    if changed:
        main.file.save(filename, ContentFile(content), save=False)
        main.save()
        Resource.raw.filter(pk=resource.pk).update(tabular_data_schema=None)
    # Also re-run when an earlier run left the file without a table (for example a failed pipeline).
    if process and (changed or not Resource.raw.filter(pk=resource.pk, has_table=True).exists()):
        transaction.on_commit(lambda: run_pipeline(resource.pk, main.pk, geo))
    if resource.status != 'published':
        transaction.on_commit(lambda: _publish(resource.pk))
    return resource


def _digest(resource_file):
    try:
        with resource_file.file.open('rb') as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except (FileNotFoundError, ValueError):
        return None


def _publish(resource_pk):
    resource = Resource.raw.get(pk=resource_pk)
    resource.status = 'published'
    resource.save()


def map_schema(schema):
    """Profile columns as text, coordinates as numbers, x-map columns marked l/b/label for the portal map."""
    schema = dict(schema)
    schema['missingValues'] = ['']
    schema['geo'] = {}
    for index, field in enumerate(schema['fields']):
        geo = standard.MAP_COLUMNS.get(field['name'])
        field.pop('geo', None)
        field['type'], field['format'] = ('number' if geo in ('l', 'b') else 'string'), 'default'
        if geo:
            field['geo'] = geo
            schema['geo'][geo] = {'col_name': field['name'], 'col_index': index}
    return schema


def run_pipeline(resource_pk, file_pk, geo):
    """The portal's own file + data pipeline, run in-process so the table and map exist when the command ends.

    Original source files keep the portal's inferred schema; a failed preview there is logged, not fatal.
    Report files get the profile's column types and must pass, or the refresh fails.
    """
    from mcod.resources.tasks.entrypoint_res_file import entrypoint_process_resource_file_validation_task
    from mcod.resources.tasks.process_resource_file_data import process_resource_file_data_task

    entrypoint_process_resource_file_validation_task.apply(args=(file_pk,), kwargs={'update_file_archive': True})
    if geo:
        resource = Resource.raw.get(pk=resource_pk)
        if not resource.tabular_data_schema:
            raise RefreshError('Zasób {}: portal nie wywnioskował schematu tabeli.'.format(resource_pk))
        Resource.raw.filter(pk=resource_pk).update(tabular_data_schema=map_schema(resource.tabular_data_schema))
        process_resource_file_data_task.apply(args=(resource_pk,), throw=True)
        Resource.raw.get(pk=resource_pk).update_es_and_rdf_db()


def operator_organization(user):
    organization, _ = Organization.objects.get_or_create(
        slug=OPERATOR['slug'],
        defaults={'title': OPERATOR['title'], 'institution_type': 'state', 'status': 'published',
                  'created_by': user, 'modified_by': user},
    )
    return organization


def publish_sources(user, process=True):
    """Each municipal snapshot as a dataset of its seeded institution, in its original layout."""
    retrieved = sources.retrieved_at()
    datasets = []
    for source in sources.SOURCES:
        organization = Organization.objects.filter(slug='jury-' + source['slug']).first()
        if organization is None:
            raise RefreshError('Brak instytucji jury-{}: najpierw uruchom seed_jury.'.format(source['slug']))
        meta = sources.source_meta(source)
        original = meta['dataset']
        url = 'https://dane.gov.pl/pl/dataset/{}'.format(source['dataset_id'])
        notes = '{}\n\nKopia lokalna zbioru {} z dane.gov.pl ({}), pobrana {} UTC. Instytucja: {}.'.format(
            original.get('notes') or original['title'], source['dataset_id'], url, retrieved,
            meta['institution']['title'])
        cc_by = original.get('license_name') == 'CC BY 4.0'
        dataset = upsert_dataset(
            'aed-src-{}'.format(source['dataset_id']), organization, user,
            title=original['title'], notes=notes, url=url, update_frequency='irregular',
            license_condition_default_cc40=True if cc_by else None,
            license_condition_source=True if cc_by else None,
        )
        resource = meta['resource']
        data_date = datetime.date.fromisoformat(resource['data_date'])
        description = '{} Oryginalny układ pliku, bez zmian. Źródło: {} (pobrano {} UTC).'.format(
            resource.get('description') or resource['title'], resource['file_url'] or resource['link'], retrieved)
        if source['file']:
            content = (sources.DATA_DIR / source['slug'] / source['file']).read_bytes()
            upsert_resource('aed-src-res-{}'.format(source['resource_id']), dataset, user, resource['title'],
                            description, data_date, filename=source['file'], content=content, process=process)
        else:
            upsert_resource('aed-src-res-{}'.format(source['resource_id']), dataset, user, resource['title'],
                            description + ' Źródło nie udostępnia anonimowego eksportu rekordów AED.',
                            data_date, link=resource['link'])
        datasets.append(dataset)
    return datasets


def publish_report(user, report_csv, report_geojson, osm_csv, process=True):
    organization = operator_organization(user)
    today = datetime.date.fromisoformat(sources.retrieved_at()[:10])
    dataset = upsert_dataset(
        REPORT_EXT, organization, user, title='Raport zbiorczy AED', notes=REPORT_NOTES,
        update_frequency='daily', license_condition_source=True,
        license_condition_custom_description=REPORT_LICENCE_NOTE,
    )
    common = ('Rekordy w wzorcowym zakresie danych AED (aed-standard/schema.json), zwalidowane przez '
              'aed-standard/validate.py. Kolumny source_records i quality_flags zawierają tablice JSON.')
    resources = [
        upsert_resource('aed-raport-csv', dataset, user, 'Raport zbiorczy AED (CSV)',
                        common + ' Podgląd mapy: longitude, latitude, etykieta name. Licencja CC BY 4.0.', today,
                        filename='raport_zbiorczy_aed.csv', content=report_csv, geo=True, process=process),
        upsert_resource('aed-raport-geojson', dataset, user, 'Raport zbiorczy AED (GeoJSON)',
                        common + ' Rekordy z CSV, które mają współrzędne, z geometrią Point (WGS84). Licencja CC BY 4.0.', today,
                        filename='raport_zbiorczy_aed.geojson', content=report_geojson, process=process),
        upsert_resource('aed-osm-csv', dataset, user, 'Punkty AED z OpenStreetMap - Polska (ODbL 1.0)',
                        'Punkty emergency=defibrillator z OpenStreetMap dla Polski (eksport OpenAEDMap {}), '
                        'w wzorcowym zakresie danych AED, bez telefonów, e-maili i danych autorów edycji. '
                        'Licencja ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/), '
                        '© OpenStreetMap contributors. Zasób porównawczy: tag operator nie potwierdza '
                        'dysponenta, nie jest częścią raportu na CC BY 4.0.'.format(sources.OSM_SOURCE_URL),
                        today, filename='osm_aed_polska.csv', content=osm_csv, geo=True, process=process),
    ]
    return dataset, resources
