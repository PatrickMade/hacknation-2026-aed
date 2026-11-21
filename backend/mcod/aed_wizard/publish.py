"""Publish a validated profile CSV as a resource in the dysponent's AED dataset."""
import csv
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.utils.html import escape

from mcod.aed_wizard import standard
from mcod.aed_wizard.models import AedPublication
from mcod.categories.models import Category
from mcod.datasets.models import Dataset
from mcod.resources.models import Resource, ResourceFile
from mcod.tags.models import Tag

LICENSES = {
    "cc0": (Dataset.LICENSE_CC0, "https://creativecommons.org/publicdomain/zero/1.0/", "CC0 1.0"),
    "cc-by": (Dataset.LICENSE_CC_BY, "https://creativecommons.org/licenses/by/4.0/", "CC BY 4.0"),
}
KEYWORDS = ("AED", "defibrylator", "zgodny ze standardem AED")
HEALTH_CATEGORY = "HEAL"


def mark():
    return "Zgodny ze standardem AED (profil PL {})".format(standard.version())


def dataset_title(organization):
    return "Defibrylatory AED - {}".format(organization.title)


def dataset_notes(organization):
    return (
        "<p>Lokalizacje i dostępność defibrylatorów AED, za które odpowiada {}. "
        "Dane w formacie wzorcowego zakresu danych AED (profil PL {}), "
        "przygotowane kreatorem „Dodaj dane AED”.</p>".format(escape(organization.title), standard.version())
    )


def aed_dataset(organization, user, license_key, update_frequency):
    """Reuse the dataset of the institution's last wizard publication, or create it."""
    code = LICENSES[license_key][0]
    dataset_ids = AedPublication.objects.filter(organization_id=organization.pk).values("dataset_id")
    dataset = Dataset.objects.filter(pk__in=dataset_ids, organization=organization).order_by("-pk").first()
    if dataset:
        dataset.update_frequency = update_frequency
        dataset.license_chosen = code
        dataset.modified_by = user
        dataset.save()
        return dataset
    dataset = Dataset.objects.create(
        title=dataset_title(organization),
        notes=dataset_notes(organization),
        organization=organization,
        update_frequency=update_frequency,
        license_chosen=code,
        status="published",
        created_by=user,
        modified_by=user,
        has_dynamic_data=False,
        has_high_value_data=False,
        has_high_value_data_from_ec_list=False,
        has_research_data=False,
        is_update_notification_enabled=False,
    )
    dataset.categories.set(Category.objects.filter(code=HEALTH_CATEGORY))
    tags = []
    for name in KEYWORDS:
        tag = Tag.objects.filter(name=name, language="pl").first()
        tags.append(tag or Tag.objects.create(name=name, language="pl", created_by=user, modified_by=user))
    dataset.tags.set(tags)
    return dataset


def tabular_schema(csv_bytes):
    """Table schema preset for the portal: text columns, numeric coordinates and map roles.

    The portal keeps a preset schema when its missingValues equal the resource's special
    signs (none here), instead of guessing types from the first rows. The roles follow the
    profile's x-map (latitude=b, longitude=l, name=label) and are set only when every record
    has coordinates, because empty cells are not valid numbers without missing values.
    """
    rows = list(csv.reader(io.StringIO(csv_bytes.decode("utf-8"), newline="")))
    header, records = rows[0], rows[1:]
    roles = standard.schema().get("x-map", {})
    with_points = all(header.count(name) for name in roles) and all(
        row[header.index("latitude")] and row[header.index("longitude")] for row in records
    )
    schema = {"fields": [], "missingValues": []}
    for index, name in enumerate(header):
        numeric = with_points and name in ("latitude", "longitude")
        field = {"name": name, "type": "number" if numeric else "string", "format": "default"}
        if with_points and name in roles:
            field["geo"] = roles[name]
            schema.setdefault("geo", {})[roles[name]] = {"col_name": name, "col_index": index}
        schema["fields"].append(field)
    return schema


def publish(organization, user, csv_bytes, records_count, warnings_count, meta):
    """meta: title, description, license (cc0|cc-by), update_frequency, data_date (date), source_name."""
    with transaction.atomic():
        dataset = aed_dataset(organization, user, meta["license"], meta["update_frequency"])
        extra = meta.get("description") or ""
        description = "<p><strong>{}</strong>. Sprawdzono walidatorem aed-standard: {} rekordów.</p>{}".format(
            mark(), records_count, "<p>{}</p>".format(escape(extra)) if extra else ""
        )
        resource = Resource.objects.create(
            title=meta["title"],
            description=description,
            dataset=dataset,
            data_date=meta["data_date"],
            status="published",
            created_by=user,
            modified_by=user,
            has_dynamic_data=False,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            contains_protected_data=False,
            tabular_data_schema=tabular_schema(csv_bytes),
        )
        filename = "aed-{}-{}.csv".format(organization.slug, meta["data_date"].isoformat())
        ResourceFile.objects.create(
            resource=resource, is_main=True, file=SimpleUploadedFile(filename, csv_bytes, content_type="text/csv")
        )
        publication = AedPublication.objects.create(
            organization_id=organization.pk,
            dataset_id=dataset.pk,
            resource_id=resource.pk,
            created_by_id=user.pk,
            records_count=records_count,
            warnings_count=warnings_count,
            standard_version=standard.version(),
            source_name=(meta.get("source_name") or "")[:500],
        )
    return publication
