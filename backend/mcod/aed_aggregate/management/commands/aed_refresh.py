"""Refresh the local "Raport zbiorczy AED" dataset and its source datasets (2026-11-21)."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mcod.aed_aggregate.publish import RefreshError
from mcod.aed_aggregate.refresh import refresh


class Command(BaseCommand):
    help = 'Load the AED source snapshots, build, validate and publish the AED report (run after seed_jury).'

    def handle(self, *args, **options):
        if settings.ENVIRONMENT != 'local':
            raise CommandError('aed_refresh is restricted to ENVIRONMENT=local.')
        try:
            result = refresh()
        except RefreshError as error:
            raise CommandError(str(error))
        self.stdout.write('Raport zbiorczy AED: dataset {dataset_id}, resources {resource_ids}, '
                          '{records} records, {osm_records} OSM points, rejected {rejected}, '
                          'OSM rejected {osm_rejected}, flags {flags}.'.format(**result))
