"""AED device registry and citizen incident reports (APP-45, 2026-11-21).

Field names follow the AED reference standard (aed-standard/schema.json).
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class AedDevice(models.Model):
    aed_id = models.UUIDField('identyfikator AED', unique=True)
    organization = models.ForeignKey(
        'organizations.Organization', models.CASCADE, related_name='aed_devices',
        verbose_name='dysponent (instytucja)',
    )
    name = models.CharField('nazwa punktu AED', max_length=300)
    location_kind = models.CharField('rodzaj lokalizacji', max_length=10, default='fixed')
    latitude = models.FloatField('szerokość geograficzna', null=True, blank=True)
    longitude = models.FloatField('długość geograficzna', null=True, blank=True)
    locality = models.CharField('miejscowość', max_length=200, blank=True)
    street_type = models.CharField('typ ulicy', max_length=30, blank=True)
    street = models.CharField('ulica', max_length=200, blank=True)
    house_number = models.CharField('numer budynku', max_length=30, blank=True)
    postcode = models.CharField('kod pocztowy', max_length=10, blank=True)
    location_description = models.TextField('opis lokalizacji', blank=True)
    access = models.CharField('dostępność', max_length=30, blank=True)
    opening_hours = models.CharField('godziny dostępności', max_length=500, blank=True)
    operational_status = models.CharField('stan urządzenia', max_length=30, blank=True)
    operator_name = models.CharField('operator', max_length=300, blank=True)
    updated_at = models.DateTimeField('zaktualizowano', auto_now=True)

    class Meta:
        verbose_name = 'urządzenie AED'
        verbose_name_plural = 'urządzenia AED'
        ordering = ('name',)

    def __str__(self):
        return '{} ({})'.format(self.name, self.address or self.aed_id)

    @property
    def address(self):
        street = ' '.join(part for part in (self.street, self.house_number) if part)
        return ', '.join(part for part in (street, ' '.join(p for p in (self.postcode, self.locality) if p)) if part)

    @property
    def page_url(self):
        return '{}/pl/aed/{}'.format(settings.BASE_URL.rstrip('/'), self.aed_id)


class AedIncidentReport(models.Model):
    TYPE_CHOICES = (
        ('closed', 'AED zamknięty lub niedostępny'),
        ('missing', 'Brak urządzenia'),
        ('damaged', 'Urządzenie uszkodzone'),
        ('wrong_data', 'Złe dane lub lokalizacja'),
    )
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = (
        (STATUS_NEW, 'nowe'),
        (STATUS_IN_PROGRESS, 'w trakcie'),
        (STATUS_RESOLVED, 'rozwiązane'),
    )

    device = models.ForeignKey(AedDevice, models.PROTECT, related_name='reports', verbose_name='urządzenie AED')
    organization = models.ForeignKey(
        'organizations.Organization', models.PROTECT, related_name='aed_reports',
        verbose_name='dysponent (instytucja)',
    )
    type = models.CharField('rodzaj problemu', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('opis')
    # blank only so retention can empty it; the public form still requires a name (services.ReportForm)
    reporter_name = models.CharField('zgłaszający', max_length=200, blank=True)
    contact = models.CharField('kontakt', max_length=200, blank=True)
    consent = models.BooleanField('zgoda RODO na kontakt', default=False)
    status = models.CharField('status', max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    dysponent_note = models.TextField('notatka dysponenta', blank=True)
    created = models.DateTimeField('przyjęto', auto_now_add=True)
    modified = models.DateTimeField('zmieniono', auto_now=True)
    resolved_at = models.DateTimeField('rozwiązano', null=True, blank=True)
    personal_data_removed_at = models.DateTimeField('usunięto dane zgłaszającego', null=True, blank=True)

    class Meta:
        verbose_name = 'zgłoszenie AED'
        verbose_name_plural = 'zgłoszenia AED'
        ordering = ('-created',)

    def __str__(self):
        return 'Zgłoszenie {} - {}'.format(self.pk, self.device.name)

    def save(self, *args, **kwargs):
        # Retention counts from resolution; reopening restarts the clock (APP-51).
        if self.status == self.STATUS_RESOLVED:
            self.resolved_at = self.resolved_at or timezone.now()
        else:
            self.resolved_at = None
        super().save(*args, **kwargs)
