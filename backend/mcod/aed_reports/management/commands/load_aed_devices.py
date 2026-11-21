"""Load AED devices of one dysponent from a CSV in the AED reference standard layout (APP-45).

The file is expected to pass aed-standard/validate.py; this command only reads the
fields the report flow needs and upserts devices by aed_id.
"""
import csv
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from mcod.aed_reports.models import AedDevice
from mcod.organizations.models import Organization

TEXT_FIELDS = ('name', 'location_kind', 'locality', 'street_type', 'street', 'house_number', 'postcode',
               'location_description', 'access', 'opening_hours', 'operational_status', 'operator_name')


def _float(value):
    return float(value) if value not in (None, '') else None


class Command(BaseCommand):
    help = 'Upsert AED devices from a standard-layout CSV for one institution (by slug).'

    def add_arguments(self, parser):
        parser.add_argument('csv_path')
        parser.add_argument('--organization', required=True, help='slug instytucji odpowiedzialnej za urządzenia')

    def handle(self, csv_path, organization, **options):
        org = Organization.objects.filter(slug=organization).first()
        if org is None:
            raise CommandError('Unknown institution slug: {}'.format(organization))
        with open(csv_path, newline='', encoding='utf-8-sig') as handle:
            rows = list(csv.DictReader(handle))
        devices = []
        for line, row in enumerate(rows, start=2):
            try:
                aed_id = uuid.UUID(row.get('aed_id') or '')
            except ValueError:
                raise CommandError('Line {}: aed_id is not a UUID'.format(line))
            if not row.get('name'):
                raise CommandError('Line {}: name is required'.format(line))
            owner = AedDevice.objects.filter(aed_id=aed_id).exclude(organization=org).first()
            if owner is not None:
                raise CommandError('Line {}: aed_id {} belongs to another institution'.format(line, aed_id))
            try:
                coords = {'latitude': _float(row.get('latitude')), 'longitude': _float(row.get('longitude'))}
            except ValueError:
                raise CommandError('Line {}: latitude/longitude must be numbers'.format(line))
            defaults = {field: (row.get(field) or '').strip() for field in TEXT_FIELDS}
            defaults.update(coords, organization=org)
            devices.append((aed_id, defaults))
        with transaction.atomic():
            created = sum(AedDevice.objects.update_or_create(aed_id=aed_id, defaults=d)[1] for aed_id, d in devices)
        self.stdout.write('AED devices for {}: {} rows, {} new.'.format(org.slug, len(devices), created))
