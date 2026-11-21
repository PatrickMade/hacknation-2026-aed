"""A wizard publication reaches the AED report on the next refresh (APP-43, 2026-11-21)."""
import datetime
import os
import shutil
import tempfile

from django.test import TestCase, override_settings

from mcod.aed_aggregate import refresh, sources
from mcod.aed_wizard import mapping, publish, readers
from mcod.aed_wizard.tests.test_mapping import CITY_CSV, CONTEXT
from mcod.aed_wizard.tests.test_views import make_user
from mcod.organizations.models import Organization

MEDIA = tempfile.mkdtemp(prefix="aed-pickup-test-")
META = {"title": "Defibrylatory AED - demo", "description": "", "license": "cc0", "update_frequency": "monthly",
        "data_date": datetime.date(2026, 11, 21), "source_name": "krosno.csv"}


def wizard_file(defaults=None):
    table = readers.read("krosno.csv", CITY_CSV)
    rules = dict(mapping.DEFAULTS, **(defaults or {}))
    return mapping.convert(table, mapping.suggest(table.columns), rules, CONTEXT)


def from_wizard(report):
    return sorted((record for record in report
                   if any(item["source_id"] == "dysponent:jury-demo" for item in record["source_records"])),
                  key=lambda record: record["aed_id"])


@override_settings(MEDIA_ROOT=MEDIA, RESOURCES_MEDIA_ROOT=os.path.join(MEDIA, "resources"))
class AggregatePickupTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = make_user("pickup.agent@mcod.local", is_staff=True, is_agent=True)
        self.org = Organization.objects.create(slug="jury-demo", title="Dysponent demonstracyjny",
                                               institution_type="other", status="published",
                                               created_by=self.user, modified_by=self.user)

    def publish(self, conversion, csv_bytes=None):
        return publish.publish(self.org, self.user, csv_bytes or conversion.csv_bytes(), len(conversion.records), 0,
                               META)

    def test_wizard_publication_appears_in_the_report_with_the_provider_ids(self):
        self.assertEqual(sources.published_records(), ([], []))
        first = wizard_file()
        self.publish(first)
        published, skipped = sources.published_records()
        self.assertEqual((len(published), skipped), (2, []))
        self.assertIsInstance(published[0]["latitude"], float)
        report = from_wizard(refresh.build(published)["report"])
        self.assertEqual(len(report), 2)
        self.assertEqual({record["aed_id"] for record in report}, {record["aed_id"] for record in first.records})
        self.assertEqual({record["operator_name"] for record in report}, {"Dysponent demonstracyjny"})

    def test_newest_publication_replaces_the_previous_values(self):
        self.publish(wizard_file())
        self.publish(wizard_file({"operational_status": "out_of_service"}))
        published, _ = sources.published_records()
        self.assertEqual(len(published), 2)
        report = from_wizard(refresh.build(published)["report"])
        self.assertEqual({record["operational_status"] for record in report}, {"out_of_service"})
        self.assertTrue(all("conflicting_sources" not in record["quality_flags"] for record in report))

    def test_foreign_source_and_missing_file_are_skipped_not_fatal(self):
        conversion = wizard_file()
        foreign = conversion.csv_bytes().replace(b"dysponent:jury-demo", b"dysponent:jury-marki")
        publication = self.publish(conversion, foreign)
        self.assertEqual(sources.published_records(), ([], [publication.resource_id]))

        publication = self.publish(conversion)
        main = publication.resource.files.get(is_main=True)
        os.remove(main.file.path)
        self.assertEqual(sources.published_records(), ([], [publication.resource_id]))
