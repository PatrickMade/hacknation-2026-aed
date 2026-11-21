"""The app's own AppConfig must load, or the daily refresh is never scheduled (APP-52, 2026-11-21)."""
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
