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


@override_settings(MEDIA_ROOT=MEDIA, RESOURCES_MEDIA_ROOT=os.path.join(MEDIA, "resources"))
class AggregatePickupTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_wizard_publication_appears_in_the_report_after_refresh(self):
        user = make_user("pickup.agent@mcod.local", is_staff=True, is_agent=True)
        org = Organization.objects.create(slug="jury-demo", title="Dysponent demonstracyjny", institution_type="other",
                                          status="published", created_by=user, modified_by=user)
        table = readers.read("krosno.csv", CITY_CSV)
        conversion = mapping.convert(table, mapping.suggest(table.columns), mapping.DEFAULTS, CONTEXT)
        self.assertEqual(sources.published_records(), [])

        publish.publish(org, user, conversion.csv_bytes(), len(conversion.records), 0, {
            "title": "Defibrylatory AED - demo", "description": "", "license": "cc0",
            "update_frequency": "monthly", "data_date": datetime.date(2026, 11, 21), "source_name": "krosno.csv",
        })

        published = sources.published_records()
        self.assertEqual(len(published), 2)
        self.assertIsInstance(published[0]["latitude"], float)
        self.assertIsInstance(published[0]["source_records"], list)
        report = refresh.build(published)["report"]
        from_wizard = [record for record in report
                       if any(item["source_id"] == "dysponent:jury-demo" for item in record["source_records"])]
        self.assertEqual(len(from_wizard), 2)
        self.assertEqual({record["operator_name"] for record in from_wizard}, {"Dysponent demonstracyjny"})
