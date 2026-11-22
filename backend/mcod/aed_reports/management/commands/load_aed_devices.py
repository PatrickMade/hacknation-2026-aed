"""Load AED devices of one dysponent from a CSV in the AED reference standard layout (APP-45).

The file is expected to pass aed-standard/validate.py; this command only reads the
fields the report flow needs and upserts devices by aed_id.
"""
import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from mcod.aed_reports.models import AedDevice
from mcod.aed_reports.services import device_fields
from mcod.organizations.models import Organization


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
                aed_id, fields = device_fields(row)
            except ValueError as error:
                raise CommandError('Line {}: {}'.format(line, error))
            owner = AedDevice.objects.filter(aed_id=aed_id).exclude(organization=org).first()
            if owner is not None:
                raise CommandError('Line {}: aed_id {} belongs to another institution'.format(line, aed_id))
            devices.append((aed_id, dict(fields, organization=org)))
        with transaction.atomic():
            created = sum(AedDevice.objects.update_or_create(aed_id=aed_id, defaults=d)[1] for aed_id, d in devices)
        self.stdout.write('AED devices for {}: {} rows, {} new.'.format(org.slug, len(devices), created))
