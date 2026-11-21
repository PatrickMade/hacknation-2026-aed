"""Publish the source snapshots and the AED report as portal datasets and resources (idempotent by ext_ident)."""
import datetime
import hashlib
import logging

from django.core.files.base import ContentFile
from django.db import transaction

from mcod.aed_aggregate import sources, standard
from mcod.categories.models import Category
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource, ResourceFile
from mcod.special_signs.models import SpecialSign
from mcod.tags.models import Tag

logger = logging.getLogger('mcod')

OPERATOR = {'slug': 'aed-operator-portalu', 'title': 'Ministerstwo Cyfryzacji - operator portalu (instancja lokalna)'}
REPORT_EXT = 'aed-raport-zbiorczy'
OSM_EXT = 'aed-osm-polska'
HEALTH_CATEGORY = 'HEAL'  # "Zdrowie", same category as the provider wizard
TAGS = ('AED', 'defibrylator', 'raport zbiorczy')
PORTAL_DATASET_URL = '/pl/dataset/{}'
REPORT_NOTES = (
    'Raport zbiorczy AED: jeden zbiór rekordów o automatycznych defibrylatorach zewnętrznych (AED) z zasobów '
    'opublikowanych w dane.gov.pl, sprowadzonych do wzorcowego zakresu danych AED (aed-standard), '
    'zwalidowanych i zdeduplikowanych. Pochodzenie każdego rekordu jest w source_records (zbiór, zasób, klucz '
    'rekordu, wydawca danych publisher_name, czas pobrania, licencja). Źródła miejskie podają tylko wydawcę '
    'danych, nie dysponenta: takie rekordy mają operator_name "nieustalony" i flagę operator_unconfirmed, dopóki '
    'dysponent nie opublikuje ich sam (kreator dysponenta). Gmina (terc) pochodzi z granic PRG. Flagi jakości '
    '(quality_flags) oznaczają też zamienione osie, punkty poza gminą dysponenta i kandydatów na duplikaty. '
    'Status działania, dostępność i godziny są "unknown", bo źródła ich nie potwierdzają. Odświeżanie: zadanie '
    'Celery codziennie o 03:30 UTC (usługa aed-beat) i polecenie aed_refresh; każde odświeżenie pobiera źródła '
    'na żywo z api.dane.gov.pl, a przy braku dostępu używa datowanej kopii. Punkty AED z OpenStreetMap są '
    'osobnym zbiorem na licencji ODbL 1.0: {osm_url}. Wzór publikacji: raport zbiorczy DGA (dane.gov.pl, zbiór '
    '4354). Instancja demonstracyjna HackNation 2026.\n\nOstatnie odświeżenie: {refresh}'
)
REPORT_LICENCE_NOTE = (
    'Zasoby "Raport zbiorczy AED" (CSV, GeoJSON): CC BY 4.0, z zachowaniem warunków źródeł: Urząd Miasta Krosna, '
    'Urząd Miejski w Przemyślu, Urząd Miasta Legionowo (CC0 1.0), Urząd Miasta Marki (CC BY 4.0). Zbiór nie '
    'zawiera danych z OpenStreetMap.'
)
OSM_NOTES = (
    'Punkty emergency=defibrillator z OpenStreetMap dla Polski (eksport krajowy OpenAEDMap {source}), w wzorcowym '
    'zakresie danych AED, bez telefonów, e-maili i danych autorów edycji. Baza danych na licencji Open Database '
    'License 1.0 (ODbL 1.0, https://opendatacommons.org/licenses/odbl/1-0/), © OpenStreetMap contributors; '
    'udostępniając bazę pochodną, zachowaj ODbL i to uznanie autorstwa. Tag operator jest tylko kandydatem, dlatego '
    'każdy rekord ma flagę operator_unconfirmed. Zbiór porównawczy do raportu zbiorczego AED: {report_url}.'
)
OSM_LICENCE_NOTE = (
    'Licencja bazy danych: Open Database License 1.0 (ODbL 1.0), https://opendatacommons.org/licenses/odbl/1-0/. '
    'Uznanie autorstwa: © OpenStreetMap contributors. Portal nie ma wyboru ODbL: obowiązuje ten opis, nie '
    'CC BY 4.0.'
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


def upsert_dataset(ext_ident, organization, user, category=None, **fields):
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
    if category:
        dataset.categories.set(Category.objects.filter(code=category))
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


def publish_sources(user, loaded, process=True):
    """Each municipal source as a dataset of its seeded institution, in its original layout: the live file when
    api.dane.gov.pl answered, else the committed snapshot (`loaded` from sources.load_sources())."""
    datasets = []
    for item in loaded:
        source, meta = item['source'], item['meta']
        organization = Organization.objects.filter(slug='jury-' + source['slug']).first()
        if organization is None:
            raise RefreshError('Brak instytucji jury-{}: najpierw uruchom seed_jury.'.format(source['slug']))
        original = meta['dataset']
        url = 'https://dane.gov.pl/pl/dataset/{}'.format(source['dataset_id'])
        notes = '{}\n\nKopia lokalna zbioru {} z dane.gov.pl ({}): {}. Instytucja: {}.'.format(
            original.get('notes') or original['title'], source['dataset_id'], url, sources.origin_note(item),
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
        description = '{} Oryginalny układ pliku, bez zmian. Źródło: {} ({}).'.format(
            resource.get('description') or resource['title'], resource['file_url'] or resource['link'],
            sources.origin_note(item))
        if source['file']:
            upsert_resource('aed-src-res-{}'.format(source['resource_id']), dataset, user, resource['title'],
                            description, data_date, filename=source['file'], content=item['content'],
                            process=process)
        else:
            upsert_resource('aed-src-res-{}'.format(source['resource_id']), dataset, user, resource['title'],
                            description + ' Źródło nie udostępnia anonimowego eksportu rekordów AED.',
                            data_date, link=resource['link'])
        datasets.append(dataset)
    return datasets


def refresh_summary(loaded, when):
    parts = ['{} ({}): {}'.format(item['meta']['institution']['title'], item['source']['dataset_id'],
                                  'na żywo z api.dane.gov.pl' if item['origin'] == 'live'
                                  else 'kopia z {}'.format(item['retrieved_at']))
             for item in loaded]
    return '{} UTC. Źródła: {}.'.format(when, '; '.join(parts))


def publish_report(user, report_csv, report_geojson, osm_csv, loaded, process=True):
    """The report (CC BY 4.0, official sources only) and OSM as its own ODbL dataset, linked both ways."""
    organization = operator_organization(user)
    today = datetime.date.fromisoformat(sources.now_utc()[:10])
    osm_dataset = upsert_dataset(
        OSM_EXT, organization, user, category=HEALTH_CATEGORY,
        title='Punkty AED z OpenStreetMap - Polska (ODbL 1.0)', notes='-', update_frequency='irregular',
        license_condition_source=True, license_condition_custom_description=OSM_LICENCE_NOTE,
        license_condition_db_or_copyrighted=OSM_LICENCE_NOTE,
    )
    dataset = upsert_dataset(
        REPORT_EXT, organization, user, category=HEALTH_CATEGORY, title='Raport zbiorczy AED',
        notes=REPORT_NOTES.format(osm_url=PORTAL_DATASET_URL.format(osm_dataset.pk),
                                  refresh=refresh_summary(loaded, sources.now_utc())),
        update_frequency='daily', license_condition_source=True,
        license_condition_custom_description=REPORT_LICENCE_NOTE, license_condition_db_or_copyrighted=None,
    )
    osm_dataset.notes = OSM_NOTES.format(source=sources.OSM_SOURCE_URL,
                                         report_url=PORTAL_DATASET_URL.format(dataset.pk))
    osm_dataset.save()
    common = ('Rekordy w wzorcowym zakresie danych AED (aed-standard/schema.json), zwalidowane przez '
              'aed-standard/validate.py. Kolumny source_records i quality_flags zawierają tablice JSON.')
    resources = [
        upsert_resource('aed-raport-csv', dataset, user, 'Raport zbiorczy AED (CSV)',
                        common + ' Podgląd mapy: longitude, latitude, etykieta name. Licencja CC BY 4.0.', today,
                        filename='raport_zbiorczy_aed.csv', content=report_csv, geo=True, process=process),
        upsert_resource('aed-raport-geojson', dataset, user, 'Raport zbiorczy AED (GeoJSON)',
                        common + ' Rekordy z CSV, które mają współrzędne, z geometrią Point (WGS84). Licencja CC BY 4.0.', today,
                        filename='raport_zbiorczy_aed.geojson', content=report_geojson, process=process),
        upsert_resource('aed-osm-csv', osm_dataset, user, 'Punkty AED z OpenStreetMap - Polska (ODbL 1.0)',
                        common + ' Licencja ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/), '
                        '© OpenStreetMap contributors. Tag operator nie potwierdza dysponenta.',
                        today, filename='osm_aed_polska.csv', content=osm_csv, geo=True, process=process),
    ]
    return dataset, osm_dataset, resources
