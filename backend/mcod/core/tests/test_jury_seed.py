"""Integration contract for the local jury seed, 2026-11-21."""
import io
import logging
import os
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client

from mcod.organizations.models import Organization
from mcod.users.models import User


CITIES = ('KROSNO', 'MARKI', 'PRZEMYSL', 'WARSZAWA', 'LEGIONOWO', 'DEMO')
PASSWORD_KEYS = ['SEED_{}_PASSWORD'.format(role) for role in ('SUPERADMIN', 'ADMIN', 'USER')]
PASSWORD_KEYS += ['SEED_{}_{}_PASSWORD'.format(city, role) for city in CITIES for role in ('AGENT', 'EDITOR')]


class JurySeedTests(TestCase):
    def setUp(self):
        # Ephemeral test credentials, never printed or used by the jury stack.
        import secrets
        self.passwords = {key: secrets.token_urlsafe(24) for key in PASSWORD_KEYS}
        self.env = patch.dict(os.environ, self.passwords)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_accounts_repeatability_and_scope(self):
        call_command('seed_jury', verbosity=0)
        self.assertEqual(User.objects.filter(email__endswith='@mcod.local').count(), 15)
        self.assertEqual(Organization.objects.count(), 6)
        user_ids = list(User.objects.order_by('email').values_list('pk', flat=True))
        org_ids = list(Organization.objects.order_by('slug').values_list('pk', flat=True))
        call_command('seed_jury', verbosity=0)
        self.assertEqual(user_ids, list(User.objects.order_by('email').values_list('pk', flat=True)))
        self.assertEqual(org_ids, list(Organization.objects.order_by('slug').values_list('pk', flat=True)))
        bootstrap = User.objects.get(email='superadmin@mcod.local')
        self.assertTrue(bootstrap.is_superuser)
        self.assertTrue(User.objects.get(email='admin@mcod.local').is_superuser)
        self.assertEqual(Organization.objects.filter(created_by=bootstrap).count(), 6)
        for role in ('superadmin', 'admin'):
            client = Client(HTTP_HOST='admin.mcod.local')
            self.assertTrue(client.login(username=role + '@mcod.local', password=self.passwords['SEED_' + role.upper() + '_PASSWORD']))
            self.assertEqual(client.get('/', secure=True).status_code, 200)
        for city in CITIES:
            slug = city.lower()
            org = Organization.objects.get(slug='jury-' + slug)
            agent = User.objects.get(email=slug + '.agent@mcod.local')
            editor = User.objects.get(email=slug + '.editor@mcod.local')
            self.assertTrue(agent.is_agent)
            self.assertEqual(agent.agent_organization_main, org)
            agent_client = Client(HTTP_HOST='admin.mcod.local')
            self.assertTrue(agent_client.login(username=agent.email, password=self.passwords['SEED_' + city + '_AGENT_PASSWORD']))
            self.assertEqual(agent_client.get('/organizations/organization/{}/change/'.format(org.pk), secure=True).status_code, 200)
            self.assertEqual(list(agent.agent_organizations.all()), [org])
            self.assertFalse(editor.is_superuser)
            self.assertTrue(editor.has_complete_staff_data, (editor.fullname, editor.phone))
            self.assertEqual(list(editor.organizations.all()), [org])
            client = Client(HTTP_HOST='admin.mcod.local')
            self.assertTrue(client.login(username=editor.email, password=self.passwords['SEED_' + city + '_EDITOR_PASSWORD']))
            own = client.get('/organizations/organization/{}/change/'.format(org.pk), secure=True)
            self.assertEqual(own.status_code, 200, getattr(own, 'url', ''))
            other = Organization.objects.exclude(pk=org.pk).first()
            denied = client.get('/organizations/organization/{}/change/'.format(other.pk), secure=True)
            self.assertIn(denied.status_code, (302, 403, 404))
            if denied.status_code == 302:
                self.assertNotIn('/login/', denied.url)  # authenticated, but the other object is hidden
        client = Client(HTTP_HOST='admin.mcod.local')
        self.assertTrue(client.login(username='user@mcod.local', password=self.passwords['SEED_USER_PASSWORD']))
        response = client.get('/organizations/organization/', secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_missing_password_refuses_without_writes(self):
        os.environ['SEED_DEMO_EDITOR_PASSWORD'] = ''
        before = (User.objects.count(), Organization.objects.count())
        with self.assertRaises(CommandError):
            call_command('seed_jury')
        self.assertEqual(before, (User.objects.count(), Organization.objects.count()))

    def test_fresh_seed_prints_no_signal_tracebacks(self):
        """A fresh seed must not print signal debug records carrying get_or_create's handled DoesNotExist."""
        records = []
        handler = logging.Handler(level=logging.DEBUG)
        handler.emit = records.append
        signals = logging.getLogger('signals')
        # Force DEBUG so the test cannot pass vacuously under settings that log signals at INFO.
        self.addCleanup(signals.setLevel, signals.level)
        signals.setLevel(logging.DEBUG)
        level = signals.level
        signals.addHandler(handler)
        self.addCleanup(signals.removeHandler, handler)
        out = io.StringIO()
        call_command('seed_jury', stdout=out)
        self.assertIn('Jury seed complete', out.getvalue())
        self.assertEqual(Organization.objects.count(), 6)
        self.assertEqual([r.getMessage() for r in records if r.exc_info and r.exc_info[0]], [])
        self.assertEqual(signals.level, level)
