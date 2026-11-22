"""The app's own AppConfig must load, or the daily refresh is never scheduled (APP-52, 2026-11-21)."""
import os
from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase

from mcod.aed_aggregate.apps import AedAggregateConfig
from mcod.aed_aggregate.tasks import TASK_NAME


class AppConfigTests(SimpleTestCase):
    def test_ready_registers_the_daily_refresh(self):
        from mcod.celeryapp import app

        self.assertIsInstance(apps.get_app_config('aed_aggregate'), AedAggregateConfig)
        entry = app.conf.beat_schedule['aed-refresh-daily']
        self.assertEqual(entry['task'], TASK_NAME)
        # Upstream rule (mcod/tests/test_celery.py): beat tasks never use the default queue.
        self.assertEqual(entry['options']['queue'], 'periodic')

    def test_aed_beat_keeps_only_aed_tasks(self):
        """Compose service aed-beat (AED_BEAT_ONLY=1) must not run the upstream portal's periodic jobs."""
        from mcod.aed_aggregate.tasks import register_beat_schedule
        from mcod.celeryapp import app

        saved = dict(app.conf.beat_schedule)
        try:
            app.conf.beat_schedule['upstream-job'] = {'task': 'mcod.datasets.tasks.create_xml_metadata_files'}
            with patch.dict(os.environ, {'AED_BEAT_ONLY': '1'}):
                register_beat_schedule()
            self.assertNotIn('upstream-job', app.conf.beat_schedule)
            self.assertTrue(all(entry['task'].startswith('mcod.aed_') for entry in app.conf.beat_schedule.values()))
            self.assertIn('aed-refresh-daily', app.conf.beat_schedule)
        finally:
            app.conf.beat_schedule.clear()
            app.conf.beat_schedule.update(saved)
