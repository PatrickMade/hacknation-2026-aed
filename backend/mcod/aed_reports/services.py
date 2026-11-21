"""Report intake and dysponent notification (APP-45, 2026-11-21)."""
import csv
import datetime
import io
import json
import logging
import math
import uuid

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import AedDevice, AedIncidentReport

logger = logging.getLogger('mcod')


class ReportForm(forms.ModelForm):
    description = forms.CharField(max_length=2000)
    reporter_name = forms.CharField(max_length=200, required=False)  # no personal data required (APP-60)
    contact = forms.CharField(max_length=200, required=False)

    class Meta:
        model = AedIncidentReport
        fields = ('type', 'description', 'reporter_name', 'contact', 'consent')

    def clean(self):
        cleaned = super().clean()
        # GDPR consent must be an explicit JSON true; strings such as "no" would pass a CheckboxInput.
        if cleaned.get('contact') and self.data.get('consent') is not True:
            self.add_error('consent', 'Podanie kontaktu wymaga zgody na przetwarzanie danych osobowych.')
        if not cleaned.get('contact'):
            cleaned['consent'] = False
        return cleaned


def get_device(aed_id):
    try:
        key = uuid.UUID(str(aed_id))
    except ValueError:
        return None
    return AedDevice.objects.select_related('organization').filter(aed_id=key).first()


def create_report(device, data):
    """Validate and store a report; return (report, None) or (None, errors)."""
    form = ReportForm(data)
    if not form.is_valid():
        return None, {field: [str(e) for e in errs] for field, errs in form.errors.items()}
    report = form.save(commit=False)
    report.device = device
    report.organization = device.organization
    report.save()
    notify_dysponent(report)
    return report, None


def notify_dysponent(report):
    org = report.organization
    recipients = {org.email} if org.email else set()
    recipients.update(org.users.filter(is_active=True).exclude(email='').values_list('email', flat=True))
    if not recipients:
        logger.warning('AED report %s: institution %s has no email recipients', report.pk, org.pk)
        return
    device = report.device
    lines = [
        'Nowe zgłoszenie dotyczące AED, za które odpowiada {}.'.format(org.title),
        '',
        'Urządzenie: {} ({})'.format(device.name, device.address or 'brak adresu'),
        'Identyfikator AED: {}'.format(device.aed_id),
        'Rodzaj problemu: {}'.format(report.get_type_display()),
        'Opis: {}'.format(report.description),
        'Zgłaszający: {}'.format(report.reporter_name or 'nie podano'),
        'Kontakt: {}'.format(report.contact if report.contact else 'nie podano'),
        '',
        'Zgłoszenie w panelu: {}/aed_reports/aedincidentreport/{}/change/'.format(
            settings.ADMIN_URL.rstrip('/'), report.pk),
    ]
    try:
        send_mail(
            'Zgłoszenie AED nr {}: {}'.format(report.pk, report.get_type_display()),
            '\n'.join(lines), settings.NO_REPLY_EMAIL, sorted(recipients),
        )
    except Exception:  # the report is stored; a mail failure must not lose it
        logger.exception('AED report %s: notification email failed', report.pk)


RETENTION_DAYS = 30


def purge_reporter_data(days=RETENTION_DAYS):
    """Remove reporter name and contact from reports resolved more than `days` ago; return how many."""
    now = timezone.now()
    return AedIncidentReport.objects.filter(
        status=AedIncidentReport.STATUS_RESOLVED,
        resolved_at__lte=now - datetime.timedelta(days=days),
        personal_data_removed_at__isnull=True,
    ).update(reporter_name='', contact='', consent=False, personal_data_removed_at=now)


# Device registry fed from AED reference standard rows (APP-45 demo files, APP-60 published report).
DEVICE_TEXT_FIELDS = ('name', 'location_kind', 'locality', 'street_type', 'street', 'house_number', 'postcode',
                      'location_description', 'access', 'opening_hours', 'operational_status', 'operator_name')
REPORT_RESOURCE = 'aed-raport-csv'


def _coordinate(value):
    if value in (None, ''):
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(value)
    return number


def device_fields(row):
    """(aed_id, field values) of one standard-layout row; raises ValueError with a readable reason."""
    try:
        aed_id = uuid.UUID(row.get('aed_id') or '')
    except ValueError:
        raise ValueError('aed_id is not a UUID')
    if not row.get('name'):
        raise ValueError('name is required')
    try:
        fields = {'latitude': _coordinate(row.get('latitude')), 'longitude': _coordinate(row.get('longitude'))}
    except ValueError:
        raise ValueError('latitude/longitude must be numbers')
    for field in DEVICE_TEXT_FIELDS:
        value = (row.get(field) or '').strip()
        limit = AedDevice._meta.get_field(field).max_length
        if limit and len(value) > limit:
            raise ValueError('{} longer than {} characters'.format(field, limit))
        fields[field] = value
    return aed_id, fields


def resolve_institution(source_records):
    """Institution responsible for a report row: the first source that names one.

    `dane:dataset:<id>` is the portal dataset `aed-src-<id>` (source snapshots published for the jury-* institutions),
    `dysponent:<slug>` is the institution that published the file itself. OSM and unknown sources name none.
    """
    from mcod.datasets.models import Dataset
    from mcod.organizations.models import Organization

    try:
        sources = json.loads(source_records or '[]')
    except ValueError:
        return None
    for source in sources if isinstance(sources, list) else []:
        source_id = str(source.get('source_id', '')) if isinstance(source, dict) else ''
        if source_id.startswith('dane:dataset:'):
            dataset = Dataset.raw.filter(ext_ident='aed-src-' + source_id.rsplit(':', 1)[1], is_removed=False).first()
            if dataset is not None:
                return dataset.organization
        elif source_id.startswith('dysponent:'):
            org = Organization.objects.filter(slug=source_id.split(':', 1)[1]).first()
            if org is not None:
                return org
    return None


def sync_report_rows(rows):
    """Upsert devices for report rows; never moves a device that another institution already holds."""
    result = {'created': 0, 'updated': 0, 'skipped_no_institution': 0, 'skipped_other_institution': 0,
              'skipped_invalid': 0}
    with transaction.atomic():
        for row in rows:
            try:
                aed_id, fields = device_fields(row)
            except ValueError:
                result['skipped_invalid'] += 1
                continue
            org = resolve_institution(row.get('source_records'))
            if org is None:
                result['skipped_no_institution'] += 1
                continue
            owner = AedDevice.objects.filter(aed_id=aed_id).values_list('organization_id', flat=True).first()
            if owner is not None and owner != org.pk:
                result['skipped_other_institution'] += 1
                continue
            _, created = AedDevice.objects.update_or_create(aed_id=aed_id, defaults=dict(fields, organization=org))
            result['created' if created else 'updated'] += 1
    return result


def report_rows():
    """Rows of the main CSV file of the published report resource, or None when it is not published."""
    from mcod.resources.models import Resource

    resource = Resource.raw.filter(ext_ident=REPORT_RESOURCE, status='published', is_removed=False).first()
    main = resource.files.filter(is_main=True).first() if resource else None
    if main is None:
        return None
    with main.file.open('rb') as handle:
        return list(csv.DictReader(io.StringIO(handle.read().decode('utf-8-sig'), newline='')))
