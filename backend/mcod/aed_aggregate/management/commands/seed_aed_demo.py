"""Seed fictional demonstration dysponenci that publish AED data through the wizard path (2026-11-22)."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mcod.aed_aggregate.demo import seed_demo
from mcod.aed_aggregate.publish import RefreshError, bootstrap_user


class Command(BaseCommand):
    help = ('Create 4 fictional demo dysponenci (labelled "dane demonstracyjne") and publish 3 AED records each '
            'through the provider wizard path; run after seed_jury and before aed_refresh.')

    def handle(self, *args, **options):
        if settings.ENVIRONMENT != 'local':
            raise CommandError('seed_aed_demo is restricted to ENVIRONMENT=local.')
        try:
            published = seed_demo(bootstrap_user())
        except RefreshError as error:
            raise CommandError(str(error))
        self.stdout.write('Demo dysponenci (dane demonstracyjne): published {}; existing ones unchanged.'.format(
            ', '.join(published) or 'none'))
