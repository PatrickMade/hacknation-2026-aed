"""AED incident reports: public API, dysponent scoping, email and QR (APP-45, 2026-11-21)."""
import hashlib
import os
import uuid

import falcon
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase
from falcon import testing

from mcod.aed_reports import qr
from mcod.aed_reports.models import AedDevice, AedIncidentReport
from mcod.aed_reports.routes import routes
from mcod.organizations.models import Organization
from mcod.showcases.models import Showcase
from mcod.users.models import User

DEMO_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'demo-jury-demo.csv')
# SHA-256 of the module matrix produced by the reference qrcodegen 1.8.0 for this URL
# (byte mode, level M, mask 2); checked against all masks and versions 1-8 during development.
REFERENCE_URL = 'https://mcod.local/pl/aed/9e908860-e09e-4ec2-a0ea-f28525974f40'
REFERENCE_SHA256 = 'b11a3a46787d585d9dad54670db2c556da202007722cb3e1a576b0cfcf9a768a'


def make_org(slug, creator, email=None):
    return Organization.objects.create(
        slug=slug, title=slug.title(), institution_type='local', status='published',
        email=email, created_by=creator, modified_by=creator,
    )


def make_staff(email, org):
    user = User.objects.create_user(email=email, password=uuid.uuid4().hex)
    user.is_staff = True
    user.state = 'active'
    user.fullname = 'Demo'
    user.phone = '000000000'
    user.save()
    user.organizations.set([org])
    return user


class AedReportsTests(TestCase):
    def setUp(self):
        app = falcon.App()
        for path, resource in routes:
            app.add_route(path, resource)
            app.add_route('/{api_version}' + path, resource)  # as mcod.routes registers them
        self.api = testing.TestClient(app)
        self.root = User.objects.create_superuser(email='root@mcod.local', password=uuid.uuid4().hex)
        self.org_a = make_org('aed-a', self.root, email='a@mcod.local')
        self.org_b = make_org('aed-b', self.root)
        self.editor_a = make_staff('a.editor@mcod.local', self.org_a)
        self.editor_b = make_staff('b.editor@mcod.local', self.org_b)
        self.device = AedDevice.objects.create(
            aed_id=uuid.uuid4(), name='AED test', organization=self.org_a,
            locality='Legionowo', street='Testowa', house_number='1', latitude=52.4, longitude=20.9,
        )

    def post_report(self, aed_id=None, **body):
        payload = {'type': 'closed', 'description': 'Szafka zamknięta', 'reporter_name': 'Jan'}
        payload.update(body)
        return self.api.simulate_post(
            '/aed/devices/{}/reports'.format(aed_id or self.device.aed_id), json=payload)

    def test_device_record_is_public_without_personal_data(self):
        response = self.api.simulate_get('/aed/devices/{}'.format(self.device.aed_id))
        self.assertEqual(response.status_code, 200)
        data = response.json['data']
        self.assertEqual(data['name'], 'AED test')
        self.assertEqual(data['organization']['title'], self.org_a.title)
        self.assertIn('/pl/aed/{}'.format(self.device.aed_id), data['report_url'])
        self.assertEqual([t['value'] for t in data['report_types']], ['closed', 'missing', 'damaged', 'wrong_data'])

    def test_unknown_or_malformed_device_is_404(self):
        self.assertEqual(self.api.simulate_get('/aed/devices/{}'.format(uuid.uuid4())).status_code, 404)
        self.assertEqual(self.api.simulate_get('/aed/devices/not-a-uuid').status_code, 404)
        self.assertEqual(self.post_report(aed_id=uuid.uuid4()).status_code, 404)

    def test_report_is_stored_for_the_responsible_dysponent_and_emailed(self):
        response = self.post_report(contact='jan@example.org', consent=True)
        self.assertEqual(response.status_code, 201, response.text)
        report = AedIncidentReport.objects.get(pk=response.json['data']['id'])
        self.assertEqual(report.organization, self.org_a)
        self.assertEqual(report.status, AedIncidentReport.STATUS_NEW)
        self.assertEqual(report.contact, 'jan@example.org')
        self.assertTrue(report.consent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(set(mail.outbox[0].to), {'a@mcod.local', 'a.editor@mcod.local'})
        self.assertIn(str(self.device.aed_id), mail.outbox[0].body)

    def test_contact_requires_explicit_consent(self):
        response = self.post_report(contact='jan@example.org')
        self.assertEqual(response.status_code, 400)
        self.assertIn('consent', response.json['errors'])
        self.assertFalse(AedIncidentReport.objects.exists())

    def test_invalid_fields_are_rejected(self):
        response = self.post_report(type='other', description='', reporter_name='')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json['errors']), {'type', 'description', 'reporter_name'})
        self.assertEqual(self.api.simulate_post(
            '/aed/devices/{}/reports'.format(self.device.aed_id), body='{', headers={'Content-Type': 'application/json'},
        ).status_code, 400)
        self.assertFalse(AedIncidentReport.objects.exists())

    def test_panel_shows_reports_only_to_the_responsible_institution(self):
        report_id = self.post_report().json['data']['id']
        changelist = '/aed_reports/aedincidentreport/'
        change = '{}{}/change/'.format(changelist, report_id)
        own = Client(HTTP_HOST='admin.mcod.local')
        own.force_login(self.editor_a)
        listing = own.get(changelist, secure=True)
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, 'AED test')
        self.assertEqual(own.get(change, secure=True).status_code, 200)
        saved = own.post(change, {'status': AedIncidentReport.STATUS_IN_PROGRESS, 'dysponent_note': 'Sprawdzamy'}, secure=True)
        self.assertEqual(saved.status_code, 302)
        self.assertEqual(AedIncidentReport.objects.get(pk=report_id).status, AedIncidentReport.STATUS_IN_PROGRESS)
        other = Client(HTTP_HOST='admin.mcod.local')
        other.force_login(self.editor_b)
        listing = other.get(changelist, secure=True)
        self.assertEqual(listing.status_code, 200)
        self.assertNotContains(listing, 'AED test')
        self.assertIn(other.get(change, secure=True).status_code, (302, 403, 404))
        self.assertEqual(AedIncidentReport.objects.get(pk=report_id).dysponent_note, 'Sprawdzamy')

    def test_qr_svg_encodes_the_device_page(self):
        response = self.api.simulate_get('/aed/devices/{}/qr.svg'.format(self.device.aed_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'image/svg+xml')
        self.assertTrue(response.text.startswith('<svg'))
        self.assertEqual(self.api.simulate_get('/1.4/aed/devices/{}/qr.svg'.format(self.device.aed_id)).status_code, 200)

    def test_qr_matrix_matches_the_reference_encoder(self):
        matrix = qr.encode(REFERENCE_URL, mask=2)
        self.assertEqual(len(matrix), 33)  # version 4
        bits = ''.join('1' if dark else '0' for row in matrix for dark in row)
        self.assertEqual(hashlib.sha256(bits.encode()).hexdigest(), REFERENCE_SHA256)
        with self.assertRaises(ValueError):
            qr.encode('x' * 300)

    def test_load_devices_command_upserts_standard_csv(self):
        org = make_org('jury-demo', self.root)
        call_command('load_aed_devices', DEMO_CSV, organization='jury-demo', verbosity=0)
        count = AedDevice.objects.filter(organization=org).count()
        self.assertGreater(count, 0)
        call_command('load_aed_devices', DEMO_CSV, organization='jury-demo', verbosity=0)
        self.assertEqual(AedDevice.objects.filter(organization=org).count(), count)

    def test_load_devices_refuses_a_device_of_another_institution(self):
        make_org('jury-demo', self.root)
        call_command('load_aed_devices', DEMO_CSV, organization='jury-demo', verbosity=0)
        with self.assertRaises(CommandError):
            call_command('load_aed_devices', DEMO_CSV, organization='aed-b', verbosity=0)
        self.assertFalse(AedDevice.objects.filter(organization=self.org_b).exists())

    def test_showcase_command(self):
        with self.assertRaises(CommandError):
            call_command('seed_aed_showcase', verbosity=0)
        call_command('seed_aed_showcase', url='https://mcod.local/pl/dataset/1/resource/2/map', verbosity=0)
        call_command('seed_aed_showcase', url='https://mcod.local/pl/dataset/1/resource/3/map', verbosity=0)
        showcase = Showcase.objects.get(title='Najbliższy AED')
        self.assertEqual(showcase.url, 'https://mcod.local/pl/dataset/1/resource/3/map')
        self.assertEqual(showcase.status, 'published')
