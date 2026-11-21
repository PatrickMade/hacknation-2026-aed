"""Report intake and dysponent notification (APP-45, 2026-11-21)."""
import logging
import uuid

from django import forms
from django.conf import settings
from django.core.mail import send_mail

from .models import AedDevice, AedIncidentReport

logger = logging.getLogger('mcod')


class ReportForm(forms.ModelForm):
    description = forms.CharField(max_length=2000)
    reporter_name = forms.CharField(max_length=200)
    contact = forms.CharField(max_length=200, required=False)

    class Meta:
        model = AedIncidentReport
        fields = ('type', 'description', 'reporter_name', 'contact', 'consent')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('contact') and not cleaned.get('consent'):
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
        'Zgłaszający: {}'.format(report.reporter_name),
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
