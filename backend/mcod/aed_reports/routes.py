"""Falcon routes of the AED reports module (APP-45)."""
from .views import DeviceQrView, DeviceReportsView, DeviceView

routes = [
    ('/aed/devices/{aed_id}', DeviceView()),
    ('/aed/devices/{aed_id}/reports', DeviceReportsView()),
    ('/aed/devices/{aed_id}/qr.svg', DeviceQrView()),
]
