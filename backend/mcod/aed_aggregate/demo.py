"""Demonstration dysponenci that publish through the provider wizard's own path (APP-57, 2026-11-22).

Every institution, street and device here is FICTIONAL and labelled "dane demonstracyjne": the records show how a
confirmed dysponent's publication reaches the AED report, they do not describe real defibrillators.
"""
import datetime
import tempfile

from mcod.aed_aggregate import sources, standard

DEMO_LABEL = 'dane demonstracyjne'
DEMO_NOTICE = ('DANE DEMONSTRACYJNE: fikcyjna instytucja i fikcyjne urządzenia AED, przygotowane do pokazu '
               'przepływu: dysponent publikuje dane, a raport zbiorczy AED je przejmuje. Nie wskazują rzeczywistych AED.')
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'

DEMO_DYSPONENCI = (
    {'slug': 'demo-szpital-sw-lukasza', 'title': 'Szpital Demonstracyjny św. Łukasza (dane demonstracyjne)',
     'locality': 'Lublin', 'postcode': '20-001', 'street': 'Demonstracyjna', 'center': (51.2465, 22.5684),
     'devices': ('Izba przyjęć', 'Hol główny, przy rejestracji', 'Parking podziemny, poziom -1')},
    {'slug': 'demo-szkola-podstawowa-100', 'title': 'Szkoła Podstawowa Przykładowa nr 100 (dane demonstracyjne)',
     'locality': 'Kraków', 'postcode': '30-001', 'street': 'Szkolna Przykładowa', 'center': (50.0614, 19.9366),
     'devices': ('Portiernia', 'Sala gimnastyczna', 'Stołówka')},
    {'slug': 'demo-centrum-sportu', 'title': 'Centrum Sportu Przykładowe (dane demonstracyjne)',
     'locality': 'Gdańsk', 'postcode': '80-001', 'street': 'Sportowa Przykładowa', 'center': (54.3520, 18.6466),
     'devices': ('Pływalnia, przy ratownikach', 'Hala sportowa, wejście A', 'Siłownia zewnętrzna')},
    {'slug': 'demo-spolka-logistyczna', 'title': 'Przykładowa Spółka Logistyczna sp. z o.o. (dane demonstracyjne)',
     'locality': 'Poznań', 'postcode': '60-001', 'street': 'Magazynowa Przykładowa', 'center': (52.4064, 16.9252),
     'devices': ('Recepcja biurowca', 'Magazyn, brama 3', 'Stołówka pracownicza')},
)


def demo_records(dysponent, when):
    """Three valid profile rows of one fictional dysponent, source_id dysponent:<slug> like the wizard's."""
    records = []
    lat0, lon0 = dysponent['center']
    for index, place in enumerate(dysponent['devices'], 1):
        local_id = 'DEMO-{}'.format(index)
        records.append({
            'aed_id': sources.aed_id('dysponent:{}:{}'.format(dysponent['slug'], local_id)),
            'name': 'AED (demo) - {}'.format(place), 'location_kind': 'fixed',
            'latitude': round(lat0 + 0.0011 * index, 7), 'longitude': round(lon0 + 0.0013 * index, 7),
            'coordinate_method': 'source', 'country_code': 'PL', 'locality': dysponent['locality'],
            'street_type': 'ulica', 'street': dysponent['street'], 'house_number': str(index),
            'postcode': dysponent['postcode'], 'location_description': '{} ({})'.format(place, DEMO_LABEL),
            'indoor': 'yes', 'access': 'public', 'opening_hours': 'Mo-Fr 07:00-19:00', 'timezone': 'Europe/Warsaw',
            'locked': 'no', 'operational_status': 'working', 'operator_name': dysponent['title'],
            'verification_method': 'operator_confirmation', 'last_verified_at': when[:10],
            'source_records': [{
                'source_id': 'dysponent:' + dysponent['slug'], 'source_record_id': local_id,
                'source_url': 'https://mcod.local/pl/dataset', 'retrieved_at': when, 'license_url': CC0,
                'attribution': '{} - {}'.format(dysponent['title'], DEMO_LABEL),
            }],
            'retrieved_at': when, 'updated_at': when, 'quality_flags': [],
        })
    return records


def seed_demo(user):
    """Create the demo institutions and publish their CSV once through mcod.aed_wizard.publish.publish."""
    from mcod.aed_wizard.models import AedPublication
    from mcod.aed_wizard.publish import publish
    from mcod.datasets.models import Dataset
    from mcod.organizations.models import Organization

    when = '2026-11-22T00:00:00Z'  # fixed, so repeated seeds publish identical files
    published = []
    for dysponent in DEMO_DYSPONENCI:
        organization, _ = Organization.objects.get_or_create(
            slug=dysponent['slug'],
            defaults={'title': dysponent['title'], 'institution_type': 'other', 'status': 'published',
                      'description': DEMO_NOTICE, 'created_by': user, 'modified_by': user},
        )
        if AedPublication.objects.filter(organization_id=organization.pk).exists():
            continue
        records = demo_records(dysponent, when)
        content, _ = standard.to_csv(records)
        with tempfile.NamedTemporaryFile(suffix='.csv') as handle:
            handle.write(content)
            handle.flush()
            errors = standard.file_errors(handle.name)
        if errors:
            raise ValueError('{}: {}'.format(dysponent['slug'], '; '.join(errors[:3])))
        publication = publish(organization, user, content, len(records), 0, {
            'title': 'Defibrylatory AED - {}'.format(dysponent['title']), 'description': DEMO_NOTICE,
            'license': 'cc0', 'update_frequency': 'irregular', 'data_date': datetime.date(2026, 11, 22),
            'source_name': 'seed_aed_demo ({})'.format(DEMO_LABEL),
        })
        dataset = Dataset.objects.get(pk=publication.dataset_id)
        if DEMO_NOTICE not in (dataset.notes or ''):
            dataset.notes = '<p><strong>{}</strong></p>{}'.format(DEMO_NOTICE, dataset.notes or '')
            dataset.save()
        published.append(organization.slug)
    return published
