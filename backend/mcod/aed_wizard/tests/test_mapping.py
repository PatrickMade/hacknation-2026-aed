"""Mapping and validation contract of the AED provider wizard (APP-43, 2026-11-21).

Inputs are synthetic rows in the layouts of the municipal AED datasets on dane.gov.pl.
"""
import io
import json
from unittest import mock

from django.test import SimpleTestCase

from mcod.aed_wizard import mapping, readers, standard

CONTEXT = {
    "org_slug": "jury-demo",
    "operator_name": "Dysponent demonstracyjny",
    "source_url": "https://mcod.local/pl/institution/1",
    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "data_date": "2026-11-21",
    "now": "2026-11-21T18:00:00Z",
}
# Semicolon, Polish headers with stray spaces, decimal commas, one address column (Krosno-like).
CITY_CSV = (
    "Długość geograficzna; Szerokość geograficzna; Nazwa; Lokalizacja; Adres; Numer Id; Godziny\r\n"
    "21,7203;49,7188;Defibrylator;Kryta pływalnia;ul. Jasna 3, 38-400 Krosno;1;całodobowo\r\n"
    "21,7113;49,7190;Defibrylator;Kampus, portiernia;ul. Wyspiańskiego 20, 38-400 Krosno;2;Mo-Fr 08:00-16:00\r\n"
).encode("cp1250")
# Whole rows quoted as one cell and latitude/longitude swapped (Marki-like).
SWAPPED_CSV = (
    '"Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id"\r\n'
    '"52.326697, 21.107557,""Defibrylator"",""Urząd Miasta"",""Al. Piłsudskiego 95, 05-270 Marki"",""1"""\r\n'
    '"52.323960, 21.098185,""Defibrylator"",""Szkoła Podstawowa"",""ul. Okólna 14, 05-270 Marki"",""2"""\r\n'
).encode("utf-8")


def convert(table, swap_axes=False, **overrides):
    rules = mapping.suggest(table.columns)
    rules.update(overrides)
    return mapping.convert(table, rules, mapping.DEFAULTS, CONTEXT, swap_axes=swap_axes)


class MappingTests(SimpleTestCase):
    def test_city_layout_converts_to_a_valid_profile_file(self):
        table = readers.read("krosno.csv", CITY_CSV)
        rules = mapping.suggest(table.columns)
        self.assertEqual(rules["latitude"], "Szerokość geograficzna")
        self.assertEqual(rules["longitude"], "Długość geograficzna")
        self.assertEqual(rules["name"], "Lokalizacja")
        self.assertEqual(rules[mapping.SOURCE_ID], "Numer Id")
        result = convert(table)
        self.assertEqual(standard.validate_bytes(result.csv_bytes()), [])
        first, second = result.records
        self.assertEqual((first["latitude"], first["longitude"]), ("49.7188", "21.7203"))
        self.assertEqual((first["street_type"], first["street"], first["house_number"]), ("ulica", "Jasna", "3"))
        self.assertEqual((first["postcode"], first["locality"]), ("38-400", "Krosno"))
        self.assertEqual((first["opening_hours"], first["timezone"]), ("24/7", "Europe/Warsaw"))
        self.assertEqual(second["opening_hours"], "Mo-Fr 08:00-16:00")
        sources = json.loads(first["source_records"])
        self.assertEqual(sources[0]["source_id"], "dysponent:jury-demo")
        self.assertEqual(sources[0]["source_record_id"], "1")
        self.assertEqual(result.generated_ids, 2)
        self.assertEqual(result.csv_bytes()[-2:], b"\r\n")

    def test_identifiers_are_stable_for_the_same_source(self):
        table = readers.read("krosno.csv", CITY_CSV)
        first = [record["aed_id"] for record in convert(table).records]
        again = [record["aed_id"] for record in convert(readers.read("krosno.csv", CITY_CSV)).records]
        self.assertEqual(first, again)
        self.assertEqual(len(set(first)), 2)

    def test_swapped_axes_are_reported_and_can_be_fixed(self):
        table = readers.read("marki.csv", SWAPPED_CSV)
        self.assertEqual(len(table.columns), 6)
        errors = standard.validate_bytes(convert(table).csv_bytes())
        self.assertEqual({(error["row"], error["field"]) for error in errors},
                         {(1, "latitude/longitude"), (2, "latitude/longitude")})
        self.assertIn("poza orientacyjną ramką Polski", errors[0]["message"])
        warnings = convert(table).warnings
        self.assertTrue(all("zamienione osie" in item["message"] for item in warnings))
        fixed = convert(table, swap_axes=True)
        self.assertEqual(standard.validate_bytes(fixed.csv_bytes()), [])
        self.assertEqual((fixed.records[0]["latitude"], fixed.records[0]["longitude"]), ("52.326697", "21.107557"))
        self.assertEqual(json.loads(fixed.records[0]["quality_flags"]), ["suspected_axis_swap"])

    def test_point_outside_poland_is_a_validator_error(self):
        data = "nazwa,szerokosc,dlugosc\r\nPunkt,40.0,-3.7\r\n".encode("utf-8")
        result = convert(readers.read("far.csv", data))
        errors = standard.validate_bytes(result.csv_bytes())
        self.assertEqual([(error["row"], error["field"]) for error in errors], [(1, "latitude/longitude")])
        self.assertEqual(json.loads(result.records[0]["quality_flags"]), ["outside_expected_area"])

    def test_duplicates_and_free_text_hours_are_warnings(self):
        data = (
            "nazwa,ulica,nr_budynku,miejscowosc,szerokosc,dlugosc,godziny\r\n"
            "Urząd,Piłsudskiego,41,Legionowo,52.395198,20.931382,w godzinach pracy urzędu\r\n"
            "Urząd,Piłsudskiego,41,Legionowo,52.395198,20.931382,24h\r\n"
        ).encode("utf-8")
        result = convert(readers.read("legionowo.csv", data))
        self.assertEqual(standard.validate_bytes(result.csv_bytes()), [])
        messages = [item["message"] for item in result.warnings]
        self.assertTrue(any("opening_hours_raw" in message for message in messages))
        self.assertTrue(any("duplikat rekordu 1" in message for message in messages))
        first, second = result.records
        self.assertEqual(first["opening_hours_raw"], "w godzinach pracy urzędu")
        self.assertEqual(second["opening_hours"], "24/7")
        self.assertIn("ambiguous_hours", json.loads(first["quality_flags"]))
        self.assertIn("duplicate_candidate", json.loads(first["quality_flags"]))
        self.assertIn("duplicate_candidate", json.loads(second["quality_flags"]))

    def test_missing_required_value_is_reported_per_row_and_field(self):
        data = "nazwa,szerokosc,dlugosc\r\nPunkt,52.1,21.0\r\n,52.2,21.1\r\n".encode("utf-8")
        errors = standard.validate_bytes(convert(readers.read("gap.csv", data)).csv_bytes())
        self.assertEqual(errors, [{"line": 3, "row": 2, "field": "name", "message": "wartość wymagana"}])

    def test_geojson_and_xlsx_sources(self):
        geojson = json.dumps({"type": "FeatureCollection", "features": [{
            "type": "Feature", "geometry": {"type": "Point", "coordinates": [22.7672, 49.7838]},
            "properties": {"id": 744, "name": "AED w ratuszu", "city": "Przemyśl", "phone": "16 675 21 00"},
        }]}).encode("utf-8")
        result = convert(readers.read("przemysl.geojson", geojson))
        self.assertEqual(standard.validate_bytes(result.csv_bytes()), [])
        record = result.records[0]
        self.assertEqual((record["latitude"], record["public_phone"]), ("49.7838", "+48166752100"))

        from openpyxl import Workbook

        book = Workbook()
        book.active.append(["nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna"])
        book.active.append(["Starostwo", 52.421807, 20.939056])
        book.active.cell(row=2, column=readers.MAX_COLUMNS + 500, value="far away")
        stream = io.BytesIO()
        book.save(stream)
        result = convert(readers.read("aed.xlsx", stream.getvalue()))
        self.assertEqual(standard.validate_bytes(result.csv_bytes()), [])
        self.assertEqual(result.records[0]["latitude"], "52.421807")
        self.assertLessEqual(len(readers.read("aed.xlsx", stream.getvalue()).columns), readers.MAX_COLUMNS)

    def test_unreadable_sources_are_explained(self):
        with self.assertRaisesMessage(readers.SourceError, "nie zawiera rekordów"):
            readers.read("empty.csv", b"nazwa,szerokosc\r\n")
        with self.assertRaisesMessage(readers.SourceError, "publiczny"):
            readers.fetch("http://127.0.0.1/aed.csv")


class FakeResponse:
    def __init__(self, status, location=None, body=b""):
        self.status_code = status
        self.headers = {"Location": location} if location else {"Content-Type": "text/csv"}
        self.is_redirect = location is not None
        self.raw = io.BytesIO(body)
        self.raw.read = lambda size, decode_content=True, _read=self.raw.read: _read(size)

    def raise_for_status(self):
        pass

    def close(self):
        pass


class FetchTests(SimpleTestCase):
    @mock.patch("mcod.aed_wizard.readers.check_public_host")
    @mock.patch("mcod.aed_wizard.readers.requests.get")
    def test_redirects_are_followed_and_each_hop_is_checked(self, get, check):
        get.side_effect = [
            FakeResponse(302, "https://api.dane.gov.pl/media/resources/aed.csv"),
            FakeResponse(200, body=b"nazwa,szerokosc,dlugosc\r\nPunkt,52.1,21.0\r\n"),
        ]
        name, data = readers.fetch("https://api.dane.gov.pl/resources/1,aed/file")
        self.assertEqual(name, "aed.csv")
        self.assertTrue(data.startswith(b"nazwa"))
        self.assertEqual([call.args[0] for call in check.call_args_list], ["api.dane.gov.pl", "api.dane.gov.pl"])

    @mock.patch("mcod.aed_wizard.readers.requests.get")
    def test_redirect_to_a_private_address_is_refused(self, get):
        get.return_value = FakeResponse(302, "http://127.0.0.1/admin")
        addresses = {"files.example": "93.184.215.14", "127.0.0.1": "127.0.0.1"}
        resolve = lambda host, port: [(0, 0, 0, "", (addresses[host], 0))]  # noqa: E731
        with mock.patch("mcod.aed_wizard.readers.socket.getaddrinfo", side_effect=resolve):
            with self.assertRaisesMessage(readers.SourceError, "publiczny"):
                readers.fetch("https://files.example/aed.csv")

    @mock.patch("mcod.aed_wizard.readers.check_public_host")
    @mock.patch("mcod.aed_wizard.readers.requests.get")
    def test_redirect_without_location_is_not_returned_as_a_file(self, get, check):
        response = FakeResponse(200, body=b"<html>moved</html>")
        response.status_code = 302
        get.return_value = response
        with self.assertRaisesMessage(readers.SourceError, "bez adresu docelowego"):
            readers.fetch("https://files.example/aed.csv")
