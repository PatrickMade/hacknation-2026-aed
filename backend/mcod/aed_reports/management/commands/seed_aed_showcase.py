"""Create or update the "Najbliższy AED" entry in the portal's Aplikacje (APP-45).

It links the map view of the "Raport zbiorczy AED" resource, where the portal's
existing map offers the distance (radius) filter around the user's location.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mcod.datasets.models import Dataset
from mcod.showcases.models import Showcase
from mcod.users.models import User

TITLE = 'Najbliższy AED'
DATASET_TITLE = 'Raport zbiorczy AED'
NOTES = (
    '<p>Mapa defibrylatorów AED z raportu zbiorczego. Otwórz mapę, wybierz „Moja lokalizacja” '
    'i ustaw odległość, aby zobaczyć najbliższe urządzenia. Przy każdym AED dysponent jest '
    'odpowiedzialny za dane; problem zgłosisz przez kod QR na naklejce przy urządzeniu.</p>'
)


class Command(BaseCommand):
    help = 'Create/update the "Najbliższy AED" showcase pointing at the raport zbiorczy map.'

    def add_arguments(self, parser):
        parser.add_argument('--url', help='adres mapy; domyślnie mapa pierwszego zasobu zbioru "{}"'.format(DATASET_TITLE))

    def handle(self, url=None, **options):
        dataset = Dataset.objects.filter(title__iexact=DATASET_TITLE, status='published').order_by('-pk').first()
        if url is None:
            resource = dataset and dataset.resources.filter(status='published').order_by('pk').first()
            if resource is None:
                raise CommandError('No published "{}" dataset with a resource; run the aggregator first '
                                   'or pass --url.'.format(DATASET_TITLE))
            url = '{}/pl/dataset/{},{}/resource/{},{}/map'.format(
                settings.BASE_URL.rstrip('/'), dataset.pk, dataset.slug, resource.pk, resource.slug)
        author = User.objects.filter(is_superuser=True).order_by('pk').first()
        if author is None:
            raise CommandError('No superuser to record as the author; run seed_jury first.')
        showcase = Showcase.objects.filter(title=TITLE).first() or Showcase(title=TITLE, created_by=author)
        showcase.category = 'www'
        showcase.notes = NOTES
        showcase.url = url
        showcase.author = 'Misja AED (prototyp HackNation 2026)'
        showcase.license_type = 'free'
        showcase.status = 'published'
        showcase.modified_by = author
        showcase.save()
        if dataset is not None:
            showcase.datasets.set([dataset])
        self.stdout.write('Showcase "{}" -> {}'.format(TITLE, url))
