"""dane.gov.pl compliance of the AED report: live sources, OSM dataset, category, operator, PRG (APP-57, 2026-11-22)."""
import copy
import os
import secrets
import tempfile
import urllib.error
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from mcod.aed_aggregate import aggregate, sources, standard

PASSWORD_KEYS = ['SEED_{}_PASSWORD'.format(role) for role in ('SUPERADMIN', 'ADMIN', 'USER')]
PASSWORD_KEYS += ['SEED_{}_{}_PASSWORD'.format(city, role)
                  for city in ('KROSNO', 'MARKI', 'PRZEMYSL', 'WARSZAWA', 'LEGIONOWO', 'DEMO')
                  for role in ('AGENT', 'EDITOR')]


def snapshot_api(url):
    """Answer API and file URLs from the committed snapshots, as the live portal would."""
    for source in sources.SOURCES:
        folder = sources.DATA_DIR / source['slug']
        if url.startswith('{}/datasets/{}/resources'.format(sources.API_URL, source['dataset_id'])):
            return (folder / 'resources.json').read_bytes()
        if url == '{}/datasets/{}'.format(sources.API_URL, source['dataset_id']):
            return (folder / 'dataset.json').read_bytes()
    if '/institutions/' in url:
        institution_id = url.rsplit('/', 1)[1]
        for source in sources.SOURCES:
            document = sources.load_json(source['slug'], 'institution.json')
            if document['data']['id'] == institution_id:
                return (sources.DATA_DIR / source['slug'] / 'institution.json').read_bytes()
        raise urllib.error.HTTPError(url, 404, 'not found', {}, None)
    for source in sources.SOURCES:
        meta = sources.snapshot(source)['meta']
        if source['file'] and url == meta['resource']['file_url']:
            return (sources.DATA_DIR / source['slug'] / source['file']).read_bytes()
    raise urllib.error.HTTPError(url, 404, 'not found', {}, None)


class LiveSourceTests(SimpleTestCase):
    def test_live_api_is_used_and_recorded(self):
        with patch.object(sources, 'http_get', side_effect=snapshot_api), \
                patch.object(sources, 'now_utc', return_value='2026-11-22T03:30:05Z'):
            loaded = sources.load_sources(use_live=True)
        self.assertEqual({item['origin'] for item in loaded}, {'live'})
        records = sources.official_records(loaded)
        self.assertEqual(len(records), 74)
        source = records[0]['source_records'][0]
        self.assertEqual(source['retrieved_at'], '2026-11-22T03:30:05Z')
        self.assertIn('pobrano z api.dane.gov.pl 2026-11-22T03:30:05Z', source['field_provenance']['source_records'])
        # updated_at follows the publisher's file change (resource.modified), not the fetch time.
        legionowo = next(r for r in records if r['name'] == 'Urząd Miasta Legionowo')
        self.assertEqual(legionowo['updated_at'], '2026-09-14T13:23:23Z')

    def test_unreachable_api_falls_back_to_the_dated_snapshot(self):
        with patch.object(sources, 'http_get', side_effect=urllib.error.URLError('no route to host')):
            loaded = sources.load_sources(use_live=True)
        self.assertEqual({item['origin'] for item in loaded}, {'snapshot'})
        self.assertIn('no route to host', loaded[0]['reason'])
        records = sources.official_records(loaded)
        self.assertEqual(len(records), 74)
        note = records[0]['source_records'][0]['field_provenance']['source_records']
        self.assertTrue(note.startswith('kopia z {} (api.dane.gov.pl niedostępne'.format(sources.retrieved_at())))

    def test_live_file_in_a_changed_layout_falls_back_for_that_source_only(self):
        def renamed_column(url):
            content = snapshot_api(url)
            return content.replace(b' Lokalizacja', b' Miejsce') if url.endswith('Defibrylator_jAmxQcp.csv') else content
        with patch.object(sources, 'http_get', side_effect=renamed_column):
            loaded = sources.load_sources(use_live=True)
        records = sources.official_records(loaded)
        self.assertEqual(len(records), 74)
        origins = {item['source']['slug']: item['origin'] for item in loaded}
        self.assertEqual(origins['krosno'], 'snapshot')
        self.assertIn('zmienionym układzie', loaded[0]['reason'])
        self.assertEqual({origins[slug] for slug in ('marki', 'przemysl', 'legionowo')}, {'live'})

    def test_empty_live_file_is_not_used(self):
        def empty_file(url):
            return b'' if url.endswith('.csv') else snapshot_api(url)
        with patch.object(sources, 'http_get', side_effect=empty_file):
            krosno = sources.load_source(sources.SOURCES[0])
        self.assertEqual(krosno['origin'], 'snapshot')


class OperatorAndGminaTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.records = sources.official_records()

    def record(self, dataset_id, record_id):
        return next(r for r in self.records for s in r['source_records']
                    if s['source_id'] == 'dane:dataset:{}'.format(dataset_id) and s['source_record_id'] == record_id)

    def test_operator_comes_from_the_location_text_with_a_quiet_flag(self):
        krosno = self.record(3624, '2')
        self.assertEqual(krosno['operator_name'], 'Kampus Sportowo-dydaktyczny, portiernia')
        self.assertEqual(krosno['source_records'][0]['publisher_name'], 'Urząd Miasta Krosna')
        przemysl = self.record(4581, '744')  # only a device label in the source: the publishing office stays
        self.assertEqual(przemysl['operator_name'], 'Urząd Miejski w Przemyślu')
        for record in self.records:
            self.assertIn('operator_from_location', record['quality_flags'])
            self.assertNotIn('operator_unconfirmed', record['quality_flags'])
            self.assertNotEqual(record['operator_name'], 'nieustalony')

    def test_two_different_dysponenci_are_flagged_not_overwritten(self):
        base = self.record(4581, '744')
        first, second = copy.deepcopy(base), copy.deepcopy(base)
        first['source_records'] = [{**base['source_records'][0], 'source_id': 'dysponent:a', 'source_record_id': '1'}]
        second['source_records'] = [{**base['source_records'][0], 'source_id': 'dysponent:b', 'source_record_id': '1'}]
        first.update(operator_name='Dysponent A', operator_regon='123456785', quality_flags=[])
        second.update(operator_name='Dysponent B', quality_flags=[])
        second.pop('operator_regon', None)
        merged = aggregate.deduplicate([first, second])[0]
        self.assertEqual((merged['operator_name'], merged['operator_regon']), ('Dysponent A', '123456785'))
        self.assertIn('conflicting_sources', merged['quality_flags'])

    def test_prg_boundaries_place_legionowo_points_in_legionowo(self):
        legionowo = [r for r in self.records if r['source_records'][0]['source_id'] == 'dane:dataset:40593']
        self.assertEqual(len(legionowo), 24)
        self.assertEqual({r['terc'] for r in legionowo}, {'1408011'})
        # Both points that the simplified L6 boundaries put into Wieliszew (1408052).
        for name in ('Starostwo Powiatowe', 'Centrum Szkolenia Policji'):
            self.assertEqual(next(r for r in legionowo if r['name'] == name)['terc'], '1408011')
        self.assertTrue(sources.in_gmina('1408011', 52.414488, 20.952687))
        self.assertFalse(sources.in_gmina('1408011', 52.2297, 21.0122))  # Warszawa centre

    def test_point_outside_its_gmina_is_withheld_and_swaps_are_checked_against_prg(self):
        wrong = self.record(4955, '7')  # Krosno's coordinates in the Marki file
        self.assertNotIn('latitude', wrong)
        self.assertNotIn('terc', wrong)
        self.assertIn('outside_expected_area', wrong['quality_flags'])
        swapped = self.record(4955, '1')
        self.assertEqual((swapped['latitude'], swapped['terc']), (52.326697, '1434021'))
        self.assertIn('suspected_axis_swap', swapped['quality_flags'])

    def test_confirmed_dysponent_replaces_a_derived_operator_on_merge(self):
        municipal = self.record(4581, '744')
        own = copy.deepcopy(municipal)
        own['source_records'] = [{**own['source_records'][0], 'source_id': 'dysponent:jury-przemysl',
                                  'source_record_id': 'AED-9485', 'publisher_name': 'ADM Centrum'}]
        own.update(operator_name='ADM Centrum Sp. z o.o.', quality_flags=[], operator_regon='123456785')
        for order in ([municipal, own], [own, municipal]):
            merged = aggregate.deduplicate(order)
            self.assertEqual(len(merged), 1)
            self.assertEqual((merged[0]['operator_name'], merged[0]['operator_regon']),
                             ('ADM Centrum Sp. z o.o.', '123456785'))
            self.assertNotIn('operator_from_location', merged[0]['quality_flags'])
            self.assertEqual(standard.record_errors(merged[0]), [])


class PublishComplianceTests(TestCase):
    def setUp(self):
        from django.core.management import call_command
        with patch.dict(os.environ, {key: secrets.token_urlsafe(24) for key in PASSWORD_KEYS}):
            call_command('seed_jury', verbosity=0)

    def test_osm_is_its_own_odbl_dataset_linked_to_the_report_and_both_are_health(self):
        from mcod.aed_aggregate.refresh import refresh
        from mcod.categories.models import Category
        from mcod.datasets.models import Dataset
        from mcod.resources.models import Resource

        result = refresh(process=False, use_live=False)
        self.assertEqual(set(result['sources'].values()), {'snapshot ' + sources.retrieved_at()})
        report = Dataset.raw.get(ext_ident='aed-raport-zbiorczy')
        osm = Dataset.raw.get(ext_ident='aed-osm-polska')
        self.assertEqual(Resource.raw.get(ext_ident='aed-osm-csv').dataset, osm)
        self.assertFalse(Resource.raw.filter(dataset=report, ext_ident='aed-osm-csv').exists())
        for text in (osm.license_condition_db_or_copyrighted, osm.license_condition_custom_description):
            self.assertIn('ODbL 1.0', text)
            self.assertIn('© OpenStreetMap contributors', text)
        self.assertIn('/pl/dataset/{}'.format(report.pk), osm.notes)
        self.assertIn('/pl/dataset/{}'.format(osm.pk), report.notes)
        self.assertIn('Ostatnie odświeżenie:', report.notes)
        for phrase in ('operator_from_location', 'publisher_name', '(dane demonstracyjne)', 'CC BY 4.0', 'ODbL 1.0'):
            self.assertIn(phrase, report.notes)
        self.assertNotIn('nieustalony', report.notes)
        self.assertNotIn('Każdy rekord wskazuje dysponenta', report.notes)
        self.assertTrue(Category.objects.filter(code='HEAL').exists())
        for dataset in (report, osm):
            self.assertEqual(list(dataset.categories.values_list('code', flat=True)), ['HEAL'])

    def test_demo_dysponenci_reach_the_report_as_confirmed_operators(self):
        from mcod.aed_aggregate.demo import DEMO_DYSPONENCI, DEMO_NOTICE, seed_demo
        from mcod.aed_aggregate.publish import bootstrap_user
        from mcod.aed_aggregate.refresh import build
        from mcod.datasets.models import Dataset

        user = bootstrap_user()
        self.assertEqual(len(seed_demo(user)), 4)
        self.assertEqual(seed_demo(user), [])  # idempotent
        published, skipped = sources.published_records()
        self.assertEqual((len(published), skipped), (12, []))
        report = build(published)['report']
        confirmed = {r['operator_name'] for r in report if aggregate.from_provider(r)}
        self.assertEqual(confirmed, {d['title'] for d in DEMO_DYSPONENCI})
        for record in report:
            if aggregate.from_provider(record):
                self.assertFalse(set(record['quality_flags']) & {'operator_from_location', 'operator_unconfirmed'})
                self.assertIn('dane demonstracyjne', record['operator_name'])
        for dysponent in DEMO_DYSPONENCI:
            dataset = Dataset.raw.get(organization__slug=dysponent['slug'])
            self.assertIn(DEMO_NOTICE, dataset.notes)

    def test_report_csv_passes_the_standard_with_terc_and_publisher(self):
        from mcod.aed_aggregate.refresh import build

        built = build()
        self.assertIn(b',terc,', built['report_csv'].split(b'\r\n', 1)[0])
        with tempfile.NamedTemporaryFile(suffix='.csv') as handle:
            handle.write(built['report_csv'])
            handle.flush()
            self.assertEqual(standard.file_errors(handle.name), [])
