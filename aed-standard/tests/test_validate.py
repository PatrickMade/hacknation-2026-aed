"""Acceptance tests exercise the public CLI, without network or dependencies."""

from pathlib import Path
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ValidatorTests(unittest.TestCase):
    def run_csv(self, text, *options):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_bytes(text.encode("utf-8"))
            return subprocess.run(
                [sys.executable, "-B", str(ROOT / "validate.py"), *options, str(path)],
                capture_output=True, text=True, check=False,
            )

    def altered(self, changes=None, omit=(), duplicate=False):
        with (ROOT / "example.csv").open(encoding="utf-8", newline="") as source:
            original = next(csv.DictReader(source))
        original.update(changes or {})
        row = {key: value for key, value in original.items() if key not in omit}
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
        if duplicate:
            writer.writerow(row)
        return out.getvalue()

    def test_example_passes(self):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "validate.py"), str(ROOT / "example.csv")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_conditional_and_provenance_errors_fail(self):
        source = {"source_id": "example:institution", "source_record_id": "AED-001",
                  "source_url": "https://example.org/aed/AED-001",
                  "retrieved_at": "2026-11-21T13:42:00Z",
                  "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"}
        cases = [
            ({"latitude": ""}, "para współrzędnych"),
            ({"latitude": "", "longitude": ""}, "fixed wymaga"),
            ({"latitude": "21.01", "longitude": "52.23"}, "ramką Polski"),
            ({"latitude": "52.23", "longitude": "13.0"}, "ramką Polski"),
            ({"timezone": ""}, "opening_hours wymaga"),
            ({"last_verified_at": "2026-02-30"}, "last_verified_at"),
            ({"source_records": "[]"}, "source_records"),
            ({"source_records": '["not an object"]'}, "obiektu JSON"),
            ({"source_records": json.dumps([{k: v for k, v in source.items() if k != "license_url"}])}, "license_url"),
            ({"source_records": json.dumps([{**source, "source_url": "file:///tmp/aed.csv"}])}, "source_url"),
            ({"source_records": json.dumps([{**source, "retrieved_at": "2026-11-21"}])}, "retrieved_at"),
            ({"quality_flags": '["invented_flag"]'}, "quality_flags"),
            ({"quality_flags": '[42]'}, "quality_flags"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                result = self.run_csv(self.altered(changes))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(message, result.stderr)

    def test_scalar_errors_fail(self):
        cases = [
            ("aed_id", "not-a-uuid"), ("operator_name", ""), ("operator_name", "   "),
            ("latitude", "NaN"), ("latitude", "Infinity"), ("latitude", "91"),
            ("longitude", "181"), ("latitude", "52,23"), ("latitude", "0"),
            ("coordinate_accuracy_m", "0"), ("coordinate_accuracy_m", "-1"),
            ("terc", "140801"), ("simc", "920806"), ("ulic", "1701"),
            ("postcode", "05120"), ("pediatric_pads", "yes"),
            ("indoor", "true"), ("access", "emergency"),
            ("operational_status", "available"), ("country_code", "DE"),
            ("public_email", "not-an-email"), ("public_phone", "220000000"),
            ("last_maintenance_on", "2026-02-30"), ("last_maintenance_on", "21.11.2026"),
            ("updated_at", "2026-11-21"), ("retrieved_at", "2026-11-21T13:42:00+00:00"),
            ("quality_flags", "{}"), ("quality_flags", "[NaN]"),
            ("source_records", "null"), ("source_records", "[broken"),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                result = self.run_csv(self.altered({field: value}))
                self.assertEqual(result.returncode, 1)
                self.assertIn(field, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_csv_structure_errors_fail(self):
        valid = self.altered()
        cases = [
            (self.altered(omit=("operator_name",)), "nagłówek"),
            (self.altered(duplicate=True), "powtórzony identyfikator"),
            (valid.replace("aed_id,name", "aed_id,aed_id", 1), "powtórzone nazwy"),
            (valid.replace("aed_id,name", "aed_id,imie_osoby", 1), "nieznane pola"),
            (valid.replace("aed_id,name", "aed_id,", 1), "niepuste"),
            (valid.replace("\r\n", "\n"), "CRLF"),
            (valid + "\r\n", "liczba komórek"),
            (self.altered({"model": ""}), "puste kolumny"),
        ]
        for text, message in cases:
            with self.subTest(message=message):
                result = self.run_csv(text)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_optional_projection_and_unknowns_pass(self):
        result = self.run_csv(self.altered(
            {"access": "unknown", "indoor": "unknown", "locked": "unknown"},
            omit=("pediatric_pads", "public_email", "public_phone", "opening_hours", "timezone"),
        ))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_mobile_without_coordinates_passes_but_fixed_fails(self):
        omit = ("latitude", "longitude", "coordinate_accuracy_m")
        result = self.run_csv(self.altered({"location_kind": "mobile", "coordinate_method": "unknown"}, omit=omit))
        self.assertEqual(result.returncode, 0, result.stderr)
        fixed = self.run_csv(self.altered(omit=omit))
        self.assertEqual(fixed.returncode, 1)
        self.assertIn("fixed wymaga", fixed.stderr)

    def test_template_requires_explicit_mode_and_no_records(self):
        text = (ROOT / "template.csv").read_bytes().decode("utf-8")
        self.assertEqual(self.run_csv(text, "--template").returncode, 0)
        self.assertEqual(self.run_csv(text).returncode, 1)
        self.assertEqual(self.run_csv(self.altered(), "--template").returncode, 1)


if __name__ == "__main__":
    unittest.main()
