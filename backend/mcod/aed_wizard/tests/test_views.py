"""Provider-panel publication and public validator of the AED wizard (APP-43, 2026-11-21)."""
import glob
import os
import secrets
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from mcod.aed_wizard import standard
from mcod.aed_wizard.models import AedPublication
from mcod.aed_wizard.tests.test_mapping import CITY_CSV
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource
from mcod.users.models import User

MEDIA = tempfile.mkdtemp(prefix="aed-wizard-test-")


def make_user(email, **flags):
    user = User(email=email, state="active", is_active=True, fullname="Demo: " + email, phone="000000000",
                email_confirmed=timezone.now(), is_official=flags.get("is_staff", False), **flags)
    user.set_password(secrets.token_urlsafe(24))  # ephemeral test credential, never printed
    user.save()
    return user


def form_data(form):
    data = {}
    for name, field in form.fields.items():
        value = form.initial.get(name, field.initial)
        value = value() if callable(value) else value
        if value in (None, False):
            continue
        data[name] = value.isoformat() if hasattr(value, "isoformat") else value
    return data


@override_settings(MEDIA_ROOT=MEDIA, RESOURCES_MEDIA_ROOT=os.path.join(MEDIA, "resources"))
class WizardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = make_user("bootstrap@mcod.local", is_superuser=True, is_staff=True)
        self.org = self.organization("jury-krosno", "Krosno")
        self.other = self.organization("jury-marki", "Marki")
        self.agent = make_user("krosno.agent@mcod.local", is_staff=True, is_agent=True)
        self.agent.organizations.set([self.org])
        self.agent.agent_organizations.set([self.org])

    def organization(self, slug, title):
        return Organization.objects.create(slug=slug, title=title, institution_type="local", status="published",
                                           created_by=self.admin, modified_by=self.admin)

    def upload(self, organization, data=CITY_CSV, name="krosno.csv"):
        return self.client.post(reverse("aed_wizard:source"), {
            "organization": organization.pk, "file": SimpleUploadedFile(name, data, content_type="text/csv"),
        })

    def run_wizard(self):
        response = self.upload(self.org)
        self.assertRedirects(response, reverse("aed_wizard:mapping"), fetch_redirect_response=False)
        page = self.client.get(reverse("aed_wizard:mapping"))
        self.assertContains(page, "Kryta pływalnia")
        data = form_data(page.context["form"])
        data["license"] = "cc-by"
        response = self.client.post(reverse("aed_wizard:mapping"), data)
        self.assertRedirects(response, reverse("aed_wizard:report"), fetch_redirect_response=False)
        report = self.client.get(reverse("aed_wizard:report"))
        self.assertEqual(report.context["errors"], [])
        self.assertContains(report, "Zgodny ze standardem AED")
        response = self.client.post(reverse("aed_wizard:report"), {
            "title": "Defibrylatory AED - Krosno", "description": "", "update_frequency": "monthly",
        })
        self.assertRedirects(response, reverse("aed_wizard:done"), fetch_redirect_response=False)
        return self.client.get(reverse("aed_wizard:done"))

    def test_agent_publishes_a_city_file_as_a_standard_resource(self):
        self.client.force_login(self.agent)
        done = self.run_wizard()
        self.assertContains(done, "Opublikowano")
        publication = AedPublication.objects.get()
        dataset, resource = publication.dataset, publication.resource
        self.assertEqual((publication.organization, publication.records_count), (self.org, 2))
        self.assertEqual(publication.standard_version, standard.version())
        self.assertEqual((dataset.organization, dataset.status, dataset.license_chosen),
                         (self.org, "published", Dataset.LICENSE_CC_BY))
        self.assertEqual(dataset.update_frequency, "monthly")
        self.assertEqual(list(dataset.categories.values_list("code", flat=True)), ["HEAL"])
        self.assertEqual(set(dataset.tags.values_list("name", flat=True)),
                         {"AED", "defibrylator", "zgodny ze standardem AED"})
        self.assertEqual((resource.dataset, resource.status), (dataset, "published"))
        self.assertIsNotNone(resource.data_date)
        self.assertTrue(resource.description.startswith("<p><strong>Zgodny ze standardem AED (profil PL"))
        main = resource.files.get(is_main=True)
        main.file.open("rb")
        content = main.file.read()
        main.file.close()
        self.assertEqual(standard.validate_bytes(content), [])
        self.assertIn(b"https://creativecommons.org/licenses/by/4.0/", content)
        schema = resource.tabular_data_schema
        self.assertEqual(schema["missingValues"], resource.special_signs_symbols_list)
        self.assertEqual({role: item["col_name"] for role, item in schema["geo"].items()},
                         {"b": "latitude", "l": "longitude", "label": "name"})
        types = {field["name"]: field["type"] for field in schema["fields"]}
        self.assertEqual((types["latitude"], types["longitude"], types["house_number"]), ("number", "number", "string"))

        self.run_wizard()
        self.assertEqual(AedPublication.objects.count(), 2)
        self.assertEqual(Dataset.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(Resource.objects.filter(dataset=dataset).count(), 2)

    def test_other_institution_cannot_be_selected(self):
        self.client.force_login(self.agent)
        response = self.upload(self.other)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["organization"])
        self.assertRedirects(self.client.get(reverse("aed_wizard:mapping")), reverse("aed_wizard:source"),
                             fetch_redirect_response=False)

    def test_accounts_without_institution_are_refused(self):
        outsider = make_user("outsider@mcod.local", is_staff=True)
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(reverse("aed_wizard:source")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("aed_wizard:source")).status_code, 302)

    def test_invalid_mapping_blocks_publication(self):
        self.client.force_login(self.agent)
        self.upload(self.org)
        data = form_data(self.client.get(reverse("aed_wizard:mapping")).context["form"])
        data.pop("map_latitude")
        self.client.post(reverse("aed_wizard:mapping"), data)
        report = self.client.get(reverse("aed_wizard:report"))
        self.assertTrue(report.context["errors"])
        self.assertNotContains(report, "Opublikuj zasób")
        self.client.post(reverse("aed_wizard:report"), {"title": "x", "update_frequency": "monthly"})
        self.assertFalse(AedPublication.objects.exists())

    def test_public_check_reports_without_storing_anything(self):
        before = (Dataset.objects.count(), Resource.objects.count(), AedPublication.objects.count())
        temp_files = set(glob.glob(os.path.join(tempfile.gettempdir(), "aed-check-*")))
        example = (standard.standard_dir() / "example.csv").read_bytes()
        response = self.client.post(reverse("aed_wizard:check"), {
            "file": SimpleUploadedFile("example.csv", example, content_type="text/csv")})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["result"]["valid"])
        self.assertContains(response, "zgodny z kontrolami standardu AED")
        response = self.client.post(reverse("aed_wizard:check"), {
            "file": SimpleUploadedFile("krosno.csv", CITY_CSV, content_type="text/csv")})
        self.assertIn("utf-8", response.context["result"]["errors"][0]["message"])
        city_utf8 = CITY_CSV.decode("cp1250").encode("utf-8")
        response = self.client.post(reverse("aed_wizard:check"), {
            "file": SimpleUploadedFile("krosno.csv", city_utf8, content_type="text/csv")})
        result = response.context["result"]
        self.assertFalse(result["valid"])
        self.assertIn("nieznane pola", result["errors"][0]["message"])
        self.assertGreater(result["suggested"], 0)
        self.assertEqual(before, (Dataset.objects.count(), Resource.objects.count(), AedPublication.objects.count()))
        self.assertEqual(temp_files, set(glob.glob(os.path.join(tempfile.gettempdir(), "aed-check-*"))))
        self.assertEqual(self.client.get(reverse("aed_wizard:standard_file", args=["template.csv"])).status_code, 200)
