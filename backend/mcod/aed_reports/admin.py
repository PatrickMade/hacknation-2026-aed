"""Dysponent panel for AED reports and devices, scoped to the user's institutions (APP-45)."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from . import qr
from .models import AedDevice, AedIncidentReport


class OrganizationScopedAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related('organization')
        if request.user.is_superuser:
            return queryset
        return queryset.filter(organization__in=request.user.organizations.all())

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AedIncidentReport)
class AedIncidentReportAdmin(OrganizationScopedAdmin):
    list_display = ('pk', 'created', 'device', 'type', 'status', 'organization')
    list_display_links = ('pk', 'device')
    list_filter = ('status', 'type')
    search_fields = ('device__name', 'device__aed_id', 'description')
    fields = ('device', 'device_page', 'organization', 'type', 'description', 'reporter_name',
              'contact', 'consent', 'created', 'status', 'dysponent_note')
    readonly_fields = ('device', 'device_page', 'organization', 'type', 'description', 'reporter_name',
                       'contact', 'consent', 'created')

    def device_page(self, obj):
        return format_html('<a href="{0}" target="_blank" rel="noopener">{0}</a>', obj.device.page_url)

    device_page.short_description = 'strona urządzenia'


@admin.register(AedDevice)
class AedDeviceAdmin(OrganizationScopedAdmin):
    list_display = ('name', 'aed_id', 'locality', 'organization', 'operational_status')
    search_fields = ('name', 'aed_id', 'locality', 'street')
    list_filter = (('organization', admin.RelatedOnlyFieldListFilter),)
    readonly_fields = ('qr_code', 'page')

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def page(self, obj):
        return format_html('<a href="{0}" target="_blank" rel="noopener">{0}</a>', obj.page_url)

    page.short_description = 'strona urządzenia (adres w kodzie QR)'

    def qr_code(self, obj):
        image = qr.svg(obj.page_url, 'Kod QR urządzenia {}'.format(obj.name), scale=4)
        return mark_safe('{}<p>Kod QR prowadzi do strony urządzenia z przyciskiem "Zgłoś problem". '
                         'Zapisz grafikę (prawy przycisk myszy) i umieść ją na naklejce przy AED.</p>'.format(image))

    qr_code.short_description = 'kod QR'
