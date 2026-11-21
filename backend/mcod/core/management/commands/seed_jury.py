"""Provision local jury accounts using the portal's existing roles (2026-11-21)."""
import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from mcod.organizations.models import Organization
from mcod.users.models import User


INSTITUTIONS = (
    ('krosno', 'Krosno'),
    ('marki', 'Marki'),
    ('przemysl', 'Przemyśl'),
    ('warszawa', 'Warszawa'),
    ('legionowo', 'Legionowo'),
    ('demo', 'Dysponent demonstracyjny'),
)


class Command(BaseCommand):
    help = 'Create/update the 15 local jury accounts and 6 institutions. Passwords come only from the environment.'

    def handle(self, *args, **options):
        if settings.ENVIRONMENT != 'local':
            raise CommandError('seed_jury is restricted to ENVIRONMENT=local.')
        keys = ['SUPERADMIN', 'ADMIN', 'USER']
        keys += ['{}_{}'.format(slug.upper(), role) for slug, _ in INSTITUTIONS for role in ('AGENT', 'EDITOR')]
        passwords = {key: os.environ.get('SEED_{}_PASSWORD'.format(key), '') for key in keys}
        missing = [key for key in keys if not passwords[key]]
        if missing:
            raise CommandError('Missing environment variables: ' + ', '.join('SEED_{}_PASSWORD'.format(key) for key in missing))

        # The portal logs every model signal at DEBUG with exc_info, so creating an institution inside
        # get_or_create's handled DoesNotExist printed that traceback. Signals still run; only their
        # debug log is quiet during the seed.
        signal_logger = logging.getLogger('signals')
        level = signal_logger.level
        signal_logger.setLevel(logging.INFO)
        try:
            self.seed(passwords)
        finally:
            signal_logger.setLevel(level)
        self.stdout.write('Jury seed complete: 15 accounts, 6 institutions. Passwords were not printed.')

    def seed(self, passwords):
        with transaction.atomic():
            bootstrap = self.user('superadmin', passwords['SUPERADMIN'], admin=True)
            self.user('admin', passwords['ADMIN'], admin=True)
            self.user('user', passwords['USER'], staff=False)
            for slug, title in INSTITUTIONS:
                org, _ = Organization.objects.get_or_create(
                    slug='jury-' + slug,
                    defaults={'title': title, 'institution_type': 'other' if slug == 'demo' else 'local',
                              'status': 'published', 'created_by': bootstrap, 'modified_by': bootstrap},
                )
                agent = self.user(slug + '.agent', passwords[slug.upper() + '_AGENT'], agent=True, org=org)
                agent.agent_organizations.set([org])
                self.user(slug + '.editor', passwords[slug.upper() + '_EDITOR'], org=org)

    @staticmethod
    def user(login, password, admin=False, staff=True, agent=False, org=None):
        user = User.objects.filter(email=login + '@mcod.local').first()
        if user is None:
            user = User(email=login + '@mcod.local')
        user.is_superuser = admin
        user.is_staff = staff
        user.is_agent = agent
        user.is_official = staff
        user.state = 'active'
        user.is_active = True
        user.fullname = 'Demo: ' + login
        user.phone = '000000000'  # Fictional demo contact required by the provider panel.
        user.email_confirmed = user.email_confirmed or timezone.now()
        user.agent_organization_main = org if agent else None
        user.set_password(password)
        user.save()
        user.organizations.set([org] if org else [])
        return user
