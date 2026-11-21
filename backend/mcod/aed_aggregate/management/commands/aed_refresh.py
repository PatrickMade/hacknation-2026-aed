"""Refresh the local "Raport zbiorczy AED" dataset and its source datasets (2026-11-21, live sources 2026-11-22)."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mcod.aed_aggregate.publish import RefreshError
from mcod.aed_aggregate.refresh import refresh


class Command(BaseCommand):
    help = ('Read the AED sources live from api.dane.gov.pl (dated snapshot as fallback), build, validate and '
            'publish the AED report and the OSM dataset (run after seed_jury).')

    def add_arguments(self, parser):
        parser.add_argument('--offline', action='store_true', help='use only the committed snapshots')

    def handle(self, *args, **options):
        if settings.ENVIRONMENT != 'local':
            raise CommandError('aed_refresh is restricted to ENVIRONMENT=local.')
        try:
            result = refresh(use_live=not options['offline'])
        except RefreshError as error:
            raise CommandError(str(error))
        self.stdout.write('Raport zbiorczy AED: dataset {dataset_id}, OSM dataset {osm_dataset_id}, resources '
                          '{resource_ids}, sources {sources}, {records} records, {osm_records} OSM points, rejected '
                          '{rejected}, OSM rejected {osm_rejected}, flags {flags}.'.format(**result))
