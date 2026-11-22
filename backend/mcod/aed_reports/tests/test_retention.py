"""Reporter data retention: 30 days after a report is resolved (APP-51, 2026-11-21)."""
import datetime
import uuid

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from mcod.aed_reports.models import AedDevice, AedIncidentReport
from mcod.aed_reports.services import ReportForm, purge_reporter_data
from mcod.organizations.models import Organization
from mcod.users.models import User


class RetentionTests(TestCase):
    def setUp(self):
        root = User.objects.create_superuser(email='root@mcod.local', password=uuid.uuid4().hex)
        org = Organization.objects.create(slug='aed-r', title='R', institution_type='local', status='published',
                                          created_by=root, modified_by=root)
        self.device = AedDevice.objects.create(aed_id=uuid.uuid4(), name='AED R', organization=org)

    def report(self, status=AedIncidentReport.STATUS_NEW, resolved_days_ago=None):
        report = AedIncidentReport.objects.create(
            device=self.device, organization=self.device.organization, type='closed', description='Opis zostaje',
            reporter_name='Jan', contact='jan@example.org', consent=True, status=status)
        if resolved_days_ago is not None:
            AedIncidentReport.objects.filter(pk=report.pk).update(
                resolved_at=timezone.now() - datetime.timedelta(days=resolved_days_ago))
        report.refresh_from_db()
        return report

    def test_resolving_sets_and_reopening_clears_resolved_at(self):
        report = self.report()
        self.assertIsNone(report.resolved_at)
        report.status = AedIncidentReport.STATUS_RESOLVED
        report.save()
        self.assertIsNotNone(report.resolved_at)
        first = report.resolved_at
        report.dysponent_note = 'Naprawione'
        report.save()
        self.assertEqual(report.resolved_at, first)  # unchanged while it stays resolved
        report.status = AedIncidentReport.STATUS_IN_PROGRESS
        report.save()
        self.assertIsNone(report.resolved_at)

    def test_personal_data_removed_30_days_after_resolution_only(self):
        old = self.report(AedIncidentReport.STATUS_RESOLVED, resolved_days_ago=31)
        recent = self.report(AedIncidentReport.STATUS_RESOLVED, resolved_days_ago=29)
        open_report = self.report(AedIncidentReport.STATUS_IN_PROGRESS)
        self.assertEqual(purge_reporter_data(), 1)
        old.refresh_from_db()
        self.assertEqual((old.reporter_name, old.contact, old.consent), ('', '', False))
        self.assertIsNotNone(old.personal_data_removed_at)
        self.assertEqual((old.description, old.status), ('Opis zostaje', AedIncidentReport.STATUS_RESOLVED))
        for kept in (recent, open_report):
            kept.refresh_from_db()
            self.assertEqual((kept.reporter_name, kept.contact), ('Jan', 'jan@example.org'))
            self.assertIsNone(kept.personal_data_removed_at)
        removed_at = old.personal_data_removed_at
        self.assertEqual(purge_reporter_data(), 0)  # repeatable, already cleaned stays as is
        old.refresh_from_db()
        self.assertEqual(old.personal_data_removed_at, removed_at)

    def test_command_and_celery_task_run_the_same_rule(self):
        self.report(AedIncidentReport.STATUS_RESOLVED, resolved_days_ago=40)
        call_command('purge_aed_reporter_data', verbosity=0)
        self.assertFalse(AedIncidentReport.objects.exclude(reporter_name='').exists())
        self.report(AedIncidentReport.STATUS_RESOLVED, resolved_days_ago=40)
        from mcod.aed_reports.tasks import purge_reporter_data_task
        self.assertEqual(purge_reporter_data_task(), {'cleaned': 1})

    def test_public_form_does_not_require_the_reporter_name(self):
        # Coordinator decision (APP-60): the form requires no personal data.
        form = ReportForm({'type': 'closed', 'description': 'x', 'reporter_name': ''})
        self.assertTrue(form.is_valid(), form.errors)


class BeatScheduleTests(TestCase):
    def test_retention_runs_daily_on_the_periodic_queue(self):
        from mcod.aed_reports.tasks import TASK_NAME
        from mcod.celeryapp import app

        entry = app.conf.beat_schedule['aed-reporter-data-retention']
        self.assertEqual(entry['task'], TASK_NAME)
        # Upstream rule (mcod/tests/test_celery.py): beat tasks never use the default queue (APP-53).
        self.assertEqual(entry.get('options', {}).get('queue'), 'periodic')
