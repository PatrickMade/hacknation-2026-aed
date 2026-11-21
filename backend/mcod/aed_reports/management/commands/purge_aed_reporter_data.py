"""Remove reporter personal data 30 days after an AED report is resolved (APP-51, 2026-11-21)."""
from django.core.management.base import BaseCommand

from mcod.aed_reports.services import RETENTION_DAYS, purge_reporter_data


class Command(BaseCommand):
    help = 'Blank reporter name and contact of AED reports resolved more than --days days ago.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=RETENTION_DAYS)

    def handle(self, days, **options):
        cleaned = purge_reporter_data(days=days)
        self.stdout.write('AED reports cleaned of reporter data: {}.'.format(cleaned))
