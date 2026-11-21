"""Mapping, deduplication and provenance of the AED report (APP-46, 2026-11-21)."""
import copy
import os
import tempfile
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from mcod.aed_aggregate import aggregate, sources, standard


def by_source(records, dataset_id, record_id):
    source_id = 'dane:dataset:{}'.format(dataset_id)
    return next(r for r in records for s in r['source_records']
                if s['source_id'] == source_id and s['source_record_id'] == record_id)


class MappingTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.records = sources.official_records()

    def test_every_municipal_record_is_mapped(self):
        counts = {}
        for record in self.records:
            source_id = record['source_records'][0]['source_id']
            counts[source_id] = counts.get(source_id, 0) + 1
        self.assertEqual(counts, {'dane:dataset:3624': 21, 'dane:dataset:4955': 8,
                                  'dane:dataset:4581': 21, 'dane:dataset:40593': 24})

    def test_krosno_address_is_split_and_original_kept(self):
        record = by_source(self.records, 3624, '2')
        self.assertEqual((record['street_type'], record['street'], record['house_number'], record['postcode'],
                          record['locality']), ('ulica', 'Stanisława Wyspiańskiego', '20', '38-400', 'Krosno'))
        self.assertEqual(record['source_records'][0]['original_values']['Adres'],
                         'ul. Stanisława Wyspiańskiego 20, 38-400 Krosno')
        self.assertEqual((record['latitude'], record['longitude']), (49.7190888, 21.711336))

    def test_marki_axis_swap_is_per_record_and_flagged(self):
        record = by_source(self.records, 4955, '1')
        self.assertEqual((record['latitude'], record['longitude']), (52.326697, 21.107557))
        self.assertEqual(record['quality_flags'], ['encoded_csv', 'suspected_axis_swap'])
        self.assertEqual(record['coordinate_method'], 'unknown')
        # Row 7 carries Krosno's coordinates: no swap can place it in Marki, so no position is published.
        wrong = by_source(self.records, 4955, '7')
        self.assertNotIn('latitude', wrong)
        self.assertIn('outside_expected_area', wrong['quality_flags'])
        self.assertEqual(wrong['source_records'][0]['original_values']['Długość geograficzna'], '21.72034402175176')

    def test_legionowo_codes_stay_text_and_incomplete_terc_is_flagged(self):
        record = next(r for r in self.records if r['name'] == 'Urząd Miasta Legionowo')
        self.assertEqual(record['simc'], '0920806')
        self.assertNotIn('terc', record)
        self.assertIn('teryt_incomplete', record['quality_flags'])
        self.assertTrue(record['source_records'][0]['source_record_id'].startswith('lokalny:'))

    def test_osm_mapping_drops_contacts_and_keeps_odbl(self):
        feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [19.5168185, 49.5878956]},
                   'properties': {'@osm_type': 'node', '@osm_id': 477958354, '@osm_version': 12, 'access': 'yes',
                                  'indoor': 'yes', 'operator': 'PTTK', 'phone': '+48 33 877 51 05',
                                  'email': 'someone@example.org', 'defibrillator:location': 'Na ścianie w jadalni'}}
        record = sources.osm_record(feature, '2026-11-21T17:32:40Z')
        self.assertEqual((record['access'], record['indoor'], record['operator_name']), ('public', 'yes', 'PTTK'))
        self.assertNotIn('public_phone', record)
        self.assertNotIn('public_email', record)
        source = record['source_records'][0]
        self.assertEqual((source['source_record_id'], source['license_url'], source['attribution']),
                         ('node/477958354', sources.ODBL_URL, sources.OSM_ATTRIBUTION))
        self.assertEqual(standard.record_errors(record), [])

    def test_osm_free_text_with_contacts_is_not_published(self):
        feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [21.0, 52.2]},
                   'properties': {'@osm_type': 'node', '@osm_id': 1, '@osm_version': 1, 'operator': '793-124-463',
                                  'model': '+48 723 248 042', 'name': 'Apteka',
                                  'defibrillator:location': 'Numer telefonu do portiera 513-077-416',
                                  'level': '0', 'manufacturer': 'kontakt: aed@example.org'}}
        record = sources.osm_record(feature, '2026-11-21T17:32:40Z')
        self.assertEqual(record['operator_name'], 'nieustalony (OpenStreetMap)')
        self.assertEqual((record['name'], record['level']), ('Apteka', '0'))
        for field in ('model', 'location_description', 'manufacturer'):
            self.assertNotIn(field, record)

    def test_addresses_hours_and_dates_are_not_mistaken_for_phones(self):
        for text in ('Urząd Miasta Krakowa ul. Lubelska 27 30-003 Kraków', 'Mo-Fr 08.00-16.00, Sa 09.00-13.00',
                     'sprawdzono 2023-03-07', 'przy wejściu 52.1696788 20.8122254'):
            self.assertEqual(sources.without_contacts(text), text)
        for text in ('tel. całodobowy: 134961664', '793-124-463', '+48 723 248 042'):
            self.assertIsNone(sources.without_contacts(text))


class DeduplicationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.records = sources.official_records()

    def test_shared_position_with_different_names_is_kept_and_flagged(self):
        result = aggregate.deduplicate(self.records)
        self.assertEqual(len(result), 74)
        police = [r for r in result if r['name'] in ('Komenda Powiatowa Policji', 'Straż Miejska')]
        self.assertEqual(len(police), 2)
        for record in police:
            self.assertIn('duplicate_candidate', record['quality_flags'])

    def test_same_place_from_two_sources_merges_with_both_provenances(self):
        original = by_source(self.records, 4581, '744')
        copy_from_other = copy.deepcopy(original)
        copy_from_other['source_records'][0].update(source_id='dane:dataset:99999', source_record_id='A-1')
        copy_from_other['latitude'] += 0.00005  # about 5.5 m north
        copy_from_other['public_phone'] = '+48000000000'
        merged = aggregate.deduplicate([original, copy_from_other])
        self.assertEqual(len(merged), 1)
        self.assertEqual({s['source_id'] for s in merged[0]['source_records']},
                         {'dane:dataset:4581', 'dane:dataset:99999'})
        self.assertEqual(merged[0]['public_phone'], '+48000000000')
        chosen = next(src for src in merged[0]['source_records'] if src['source_id'] == 'dane:dataset:99999')
        self.assertIn('public_phone', chosen['field_provenance'])
        reversed_order = aggregate.deduplicate([copy_from_other, original])
        self.assertEqual(merged[0]['aed_id'], reversed_order[0]['aed_id'])

    def test_same_place_twice_in_one_source_stays_two_devices(self):
        original = by_source(self.records, 4581, '744')
        second = copy.deepcopy(original)
        second['source_records'][0]['source_record_id'] = '9999'
        result = aggregate.deduplicate([original, second])
        self.assertEqual(len(result), 2)
        for record in result:
            self.assertIn('duplicate_candidate', record['quality_flags'])

    def test_conflicting_values_are_flagged_not_overwritten(self):
        original = by_source(self.records, 4581, '744')
        other = copy.deepcopy(original)
        other['source_records'][0].update(source_id='dane:dataset:99999', source_record_id='A-1')
        other['postcode'] = '00-001'
        merged = aggregate.deduplicate([original, other])[0]
        self.assertEqual(merged['postcode'], original['postcode'])
        self.assertIn('conflicting_sources', merged['quality_flags'])

    def test_same_source_identity_merges_and_ids_are_stable(self):
        result = aggregate.deduplicate(self.records + copy.deepcopy(self.records[:3]))
        self.assertEqual(len(result), 74)
        self.assertEqual([r['aed_id'] for r in result], [r['aed_id'] for r in aggregate.deduplicate(self.records)])
        self.assertEqual(len({r['aed_id'] for r in result}), 74)


class ProvenanceTests(SimpleTestCase):
    def test_every_record_names_source_licence_and_dysponent(self):
        report, rejected = aggregate.check(aggregate.deduplicate(sources.official_records()))
        self.assertEqual(rejected, [])
        for record in report:
            self.assertTrue(record['operator_name'].startswith('Urząd'))
            for source in record['source_records']:
                for key in ('source_id', 'source_record_id', 'source_url', 'retrieved_at', 'license_url',
                            'source_version', 'source_data_date', 'original_values'):
                    self.assertTrue(source.get(key), (record['name'], key))
                self.assertEqual(source['field_provenance']['operator_name'], sources.OPERATOR_NOTE)
        marki = by_source(report, 4955, '1')['source_records'][0]
        self.assertEqual(marki['license_url'], sources.CC_BY_URL)
        self.assertEqual(marki['attribution'], 'Urząd Miasta Marki, dane.gov.pl zbiór 4955')
        self.assertEqual(marki['source_url'],
                         'https://api.dane.gov.pl/media/resources/20250710/Defibrylator_GminaMiastoMarki_1.csv')
        krosno = by_source(report, 3624, '1')['source_records'][0]
        self.assertEqual(krosno['license_url'], sources.CC0_URL)
        self.assertNotIn('attribution', krosno)

    def test_report_file_passes_aed_standard_validator(self):
        report, _ = aggregate.check(aggregate.deduplicate(sources.official_records()))
        content, columns = standard.to_csv(report)
        self.assertEqual(columns[:3], ['aed_id', 'name', 'location_kind'])
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as handle:
            handle.write(content)
        self.addCleanup(os.unlink, handle.name)
        self.assertEqual(standard.file_errors(handle.name), [])

    def test_invalid_report_file_stops_the_refresh(self):
        from mcod.aed_aggregate import refresh
        from mcod.aed_aggregate.publish import RefreshError
        with patch.object(standard, 'file_errors', return_value=['nagłówek: brak wymaganych pól: name']):
            with self.assertRaises(RefreshError):
                refresh.build()

    def test_unknown_source_licence_fails_closed(self):
        source = sources.SOURCES[0]
        meta = sources.source_meta(source)
        meta['dataset']['license_name'] = 'CC BY-NC 4.0'
        with self.assertRaises(KeyError):
            sources.source_record(source, meta, '1', {}, {}, '2026-11-21T17:32:40Z')

    def test_validator_rejection_is_reported_not_published(self):
        record = copy.deepcopy(sources.official_records()[0])
        record['postcode'] = '38400'
        accepted, rejected = aggregate.check([record])
        self.assertEqual(accepted, [])
        self.assertIn('postcode', rejected[0][1][0])


class MapSchemaTests(SimpleTestCase):
    def test_x_map_columns_become_portal_map_fields(self):
        from mcod.aed_aggregate.publish import map_schema
        inferred = {'fields': [{'name': 'aed_id', 'type': 'string'}, {'name': 'name', 'type': 'string'},
                               {'name': 'latitude', 'type': 'string'}, {'name': 'longitude', 'type': 'number'},
                               {'name': 'simc', 'type': 'integer'}], 'missingValues': []}
        schema = map_schema(inferred)
        self.assertEqual(schema['geo'], {'label': {'col_name': 'name', 'col_index': 1},
                                         'b': {'col_name': 'latitude', 'col_index': 2},
                                         'l': {'col_name': 'longitude', 'col_index': 3}})
        self.assertEqual([f['type'] for f in schema['fields']], ['string', 'string', 'number', 'number', 'string'])
        self.assertEqual(schema['missingValues'], [''])


PASSWORD_KEYS = ['SEED_{}_PASSWORD'.format(role) for role in ('SUPERADMIN', 'ADMIN', 'USER')]
PASSWORD_KEYS += ['SEED_{}_{}_PASSWORD'.format(city, role)
                  for city in ('KROSNO', 'MARKI', 'PRZEMYSL', 'WARSZAWA', 'LEGIONOWO', 'DEMO')
                  for role in ('AGENT', 'EDITOR')]


class PublishTests(TestCase):
    def test_refresh_creates_source_and_report_datasets_idempotently(self):
        import secrets
        from django.core.management import call_command
        from mcod.aed_aggregate.refresh import refresh
        from mcod.datasets.models import Dataset
        from mcod.resources.models import Resource

        with patch.dict(os.environ, {key: secrets.token_urlsafe(24) for key in PASSWORD_KEYS}):
            call_command('seed_jury', verbosity=0)
        result = refresh(process=False)
        self.assertEqual(result['records'], 74)
        self.assertEqual(result['osm_records'], 18298)
        sources_ = Dataset.raw.filter(ext_ident__startswith='aed-src-')
        self.assertEqual(sorted(d.organization.slug for d in sources_),
                         ['jury-krosno', 'jury-legionowo', 'jury-marki', 'jury-przemysl', 'jury-warszawa'])
        report = Dataset.raw.get(ext_ident='aed-raport-zbiorczy')
        self.assertEqual(report.organization.slug, 'aed-operator-portalu')
        self.assertEqual(report.license_name, 'CC BY 4.0')
        self.assertIn('ODbL 1.0', report.license_condition_custom_description)
        resources = {r.ext_ident: r for r in Resource.raw.filter(dataset=report)}
        self.assertEqual(set(resources), {'aed-raport-csv', 'aed-raport-geojson', 'aed-osm-csv'})
        self.assertIn('ODbL', resources['aed-osm-csv'].title)
        main = resources['aed-raport-csv'].files.get(is_main=True)
        with main.file.open('rb') as handle:
            self.assertTrue(handle.read().startswith(b'aed_id,name,location_kind,latitude,longitude'))
        warsaw = Resource.raw.get(ext_ident='aed-src-res-2512040')
        self.assertTrue(warsaw.link.startswith('https://dane.um.warszawa.pl/'))
        counts = (Dataset.raw.count(), Resource.raw.count())
        refresh(process=False)
        self.assertEqual(counts, (Dataset.raw.count(), Resource.raw.count()))


class ResourceReplacementTests(TestCase):
    """on_commit callbacks run immediately, so the draft -> published step and file replacement are exercised."""

    @patch('mcod.aed_aggregate.publish.transaction.on_commit', side_effect=lambda func: func())
    def test_changed_content_replaces_the_file_of_the_same_published_resource(self, _on_commit):
        import secrets
        from django.core.management import call_command
        from mcod.aed_aggregate import publish

        with patch.dict(os.environ, {key: secrets.token_urlsafe(24) for key in PASSWORD_KEYS}):
            call_command('seed_jury', verbosity=0)
        user = publish.bootstrap_user()
        dataset = publish.upsert_dataset('aed-test', publish.operator_organization(user), user,
                                         title='Test AED', notes='Zbiór testowy AED.')
        first = publish.upsert_resource('aed-test-csv', dataset, user, 'Test', 'Opis testowy zasobu.', None,
                                        filename='t.csv', content=b'a\r\n1\r\n', process=False)
        first.refresh_from_db()
        self.assertEqual(first.status, 'published')
        second = publish.upsert_resource('aed-test-csv', dataset, user, 'Test', 'Opis testowy zasobu.', None,
                                         filename='t.csv', content=b'a\r\n2\r\n', process=False)
        self.assertEqual(first.pk, second.pk)
        main = second.files.get(is_main=True)
        with main.file.open('rb') as handle:
            self.assertEqual(handle.read(), b'a\r\n2\r\n')
