"""Public Falcon endpoints for AED device records and incident reports (APP-45)."""
import json

import falcon

from . import qr
from .models import AedIncidentReport
from .services import create_report, get_device


def _json(resp, status, payload):
    resp.status = status
    resp.content_type = 'application/json'
    resp.text = json.dumps(payload, ensure_ascii=False)


def _device_or_404(aed_id):
    device = get_device(aed_id)
    if device is None:
        raise falcon.HTTPNotFound()
    return device


class DeviceView:
    def on_get(self, req, resp, aed_id, **kwargs):
        device = _device_or_404(aed_id)
        _json(resp, falcon.HTTP_200, {'data': {
            'aed_id': str(device.aed_id),
            'name': device.name,
            'address': device.address,
            'location_description': device.location_description,
            'access': device.access,
            'opening_hours': device.opening_hours,
            'operational_status': device.operational_status,
            'operator_name': device.operator_name,
            'latitude': device.latitude,
            'longitude': device.longitude,
            'organization': {'id': device.organization_id, 'title': device.organization.title},
            'report_url': device.page_url,
            'qr_url': '/aed/devices/{}/qr.svg'.format(device.aed_id),
            'report_types': [{'value': v, 'label': label} for v, label in AedIncidentReport.TYPE_CHOICES],
        }})


class DeviceReportsView:
    def on_post(self, req, resp, aed_id, **kwargs):
        device = _device_or_404(aed_id)
        try:
            data = json.loads(req.bounded_stream.read().decode('utf-8') or '{}')
        except (ValueError, UnicodeDecodeError):
            data = None
        if not isinstance(data, dict):
            return _json(resp, falcon.HTTP_400, {'errors': {'body': ['Niepoprawny JSON.']}})
        report, errors = create_report(device, data)
        if errors:
            return _json(resp, falcon.HTTP_400, {'errors': errors})
        _json(resp, falcon.HTTP_201, {'data': {'id': report.pk, 'status': report.status}})


class DeviceQrView:
    def on_get(self, req, resp, aed_id, **kwargs):
        device = _device_or_404(aed_id)
        resp.status = falcon.HTTP_200
        resp.content_type = 'image/svg+xml'
        resp.text = qr.svg(device.page_url, 'Kod QR: zgłoś problem z AED {}'.format(device.name))
