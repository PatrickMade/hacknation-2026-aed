"""Register a device for every record of the published "Raport zbiorczy AED" (APP-60, 2026-11-22).

Run after `aed_refresh`. Each record's responsible institution comes from its source_records; see
services.resolve_institution. Reruns update devices in place.
"""
from django.core.management.base import BaseCommand, CommandError

from mcod.aed_reports.services import report_rows, sync_report_rows


class Command(BaseCommand):
    help = 'Upsert AED devices from the published Raport zbiorczy AED CSV, keyed by aed_id.'

    def handle(self, **options):
        rows = report_rows()
        if rows is None:
            raise CommandError('The "Raport zbiorczy AED" CSV resource is not published; run aed_refresh first.')
        result = sync_report_rows(rows)
        self.stdout.write('AED devices from the report: {} rows, {} new, {} updated, {} without dysponent, '
                          '{} held by another institution, {} invalid.'.format(
                              len(rows), result['created'], result['updated'], result['skipped_no_institution'],
                              result['skipped_other_institution'], result['skipped_invalid']))
