"""Device registry from the published "Raport zbiorczy AED" and optional reporter name (APP-60, 2026-11-22)."""
import json
import os
import secrets
import uuid
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from mcod.aed_reports.models import AedDevice, AedIncidentReport
from mcod.aed_reports.services import create_report, sync_report_rows
from mcod.organizations.models import Organization
from mcod.users.models import User

PASSWORD_KEYS = ['SEED_{}_PASSWORD'.format(role) for role in ('SUPERADMIN', 'ADMIN', 'USER')]
PASSWORD_KEYS += ['SEED_{}_{}_PASSWORD'.format(city, role)
                  for city in ('KROSNO', 'MARKI', 'PRZEMYSL', 'WARSZAWA', 'LEGIONOWO', 'DEMO')
                  for role in ('AGENT', 'EDITOR')]


def row(source_id, aed_id=None, name='AED z raportu'):
    return {
        'aed_id': aed_id or str(uuid.uuid4()), 'name': name, 'latitude': '52.40', 'longitude': '20.92',
        'locality': 'Legionowo', 'source_records': json.dumps([{'source_id': source_id, 'source_record_id': '1'}]),
    }


class SyncRowsTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(email='root@mcod.local', password=uuid.uuid4().hex)
        self.org = Organization.objects.create(slug='jury-demo', title='Demo', institution_type='other',
                                               status='published', created_by=self.root, modified_by=self.root)
        self.other = Organization.objects.create(slug='jury-marki', title='Marki', institution_type='local',
                                                 status='published', created_by=self.root, modified_by=self.root)

    def test_dysponent_source_assigns_that_institution_and_reruns_update(self):
        first = row('dysponent:jury-demo')
        result = sync_report_rows([first, row('osm'), row('dysponent:nieznana')])
        self.assertEqual((result['created'], result['skipped_no_institution']), (1, 2))
        device = AedDevice.objects.get(aed_id=first['aed_id'])
        self.assertEqual(device.organization, self.org)
        first['name'] = 'AED po zmianie'
        result = sync_report_rows([first])
        self.assertEqual((result['created'], result['updated']), (0, 1))
        self.assertEqual(AedDevice.objects.get(aed_id=first['aed_id']).name, 'AED po zmianie')

    def test_device_of_another_institution_is_not_reassigned(self):
        taken = AedDevice.objects.create(aed_id=uuid.uuid4(), name='Cudzy', organization=self.other)
        result = sync_report_rows([row('dysponent:jury-demo', aed_id=str(taken.aed_id))])
        self.assertEqual(result['skipped_other_institution'], 1)
        taken.refresh_from_db()
        self.assertEqual((taken.organization, taken.name), (self.other, 'Cudzy'))

    def test_report_without_name_or_contact_is_accepted(self):
        device = AedDevice.objects.create(aed_id=uuid.uuid4(), name='AED', organization=self.org)
        report, errors = create_report(device, {'type': 'closed', 'description': 'Szafka zamknięta'})
        self.assertIsNone(errors)
        self.assertEqual((report.reporter_name, report.contact, report.consent), ('', '', False))
        _, errors = create_report(device, {'type': 'closed', 'description': 'x', 'contact': 'a@example.org'})
        self.assertIn('consent', errors)
        self.assertTrue(all('Zgłaszający: nie podano' in m.body for m in mail.outbox[:1]))


class ReportDevicesIntegrationTests(TestCase):
    @patch('mcod.aed_aggregate.publish.transaction.on_commit', side_effect=lambda func: func())
    def test_every_report_record_with_a_dysponent_gets_a_device(self, _on_commit):
        from mcod.aed_aggregate.refresh import refresh
        from mcod.datasets.models import Dataset

        with patch.dict(os.environ, {key: secrets.token_urlsafe(24) for key in PASSWORD_KEYS}):
            call_command('seed_jury', verbosity=0)
        result = refresh(process=False)
        call_command('load_aed_report_devices', verbosity=0)
        devices = AedDevice.objects.select_related('organization')
        self.assertGreater(devices.count(), 0)
        self.assertLessEqual(devices.count(), result['records'])
        source_orgs = {d.ext_ident: d.organization.slug for d in Dataset.raw.filter(ext_ident__startswith='aed-src-')}
        self.assertTrue(all(d.organization.slug in source_orgs.values() for d in devices))
        count = devices.count()
        call_command('load_aed_report_devices', verbosity=0)
        self.assertEqual(AedDevice.objects.count(), count)
        device = devices.first()
        report, errors = create_report(device, {'type': 'damaged', 'description': 'Ekran nie działa'})
        self.assertIsNone(errors)
        self.assertEqual(report.organization, device.organization)
        self.assertFalse(AedIncidentReport.objects.exclude(organization=device.organization).exists())
