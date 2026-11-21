"""Check the delivered files agree on the public 43-field contract."""

import csv
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
        self.fields = self.schema["fields"]
        self.names = [field["name"] for field in self.fields]

    def test_schema_and_csv_headers(self):
        self.assertEqual(len(self.names), 43)
        self.assertEqual(len(set(self.names)), 43)
        self.assertEqual(self.schema["primaryKey"], ["aed_id"])
        self.assertEqual(self.schema["missingValues"], [""])
        self.assertEqual(self.schema["fieldsMatch"], "superset")
        for filename in ("template.csv", "example.csv"):
            raw = (ROOT / filename).read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            text = raw.decode("utf-8")
            self.assertNotIn("\n", text.replace("\r\n", ""))
            with (ROOT / filename).open(encoding="utf-8", newline="") as source:
                rows = list(csv.reader(source))
            self.assertEqual(rows[0], self.names)
            self.assertEqual(len(rows), 1 if filename == "template.csv" else 2)

    def test_dictionary_matches_schema_without_formulas_or_errors(self):
        with ZipFile(ROOT / "field-dictionary.xlsx") as book:
            self.assertIsNone(book.testzip())
            sheet = ET.fromstring(book.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall("s:sheetData/s:row", NS):
            cells = row.findall("s:c", NS)
            self.assertEqual(len(cells), 7)
            for cell in cells:
                self.assertIsNone(cell.find("s:f", NS))
                self.assertNotEqual(cell.get("t"), "e")
            rows.append(["".join(cell.itertext()) for cell in cells])
        self.assertEqual(len(rows), 44)
        self.assertEqual(rows[0], ["Pole", "Polska etykieta", "Typ", "Wymagalność",
                                  "Format lub dozwolone wartości", "Przykład", "Opis"])
        requirement = {"R": "wymagane", "O": "opcjonalne", "C": "warunkowe"}
        for field, row in zip(self.fields, rows[1:]):
            self.assertEqual(row[:4], [field["name"], field["title"], field["type"],
                                      requirement[field["x-requirement"]]])
            self.assertEqual(row[5:], [field["example"], field["description"]])
            self.assertTrue(row[4])
            for value in field.get("constraints", {}).get("enum", []):
                self.assertIn(value, row[4])

    def test_all_fields_have_six_explicit_source_mappings(self):
        with (ROOT / "mappings.csv").open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            self.assertEqual(reader.fieldnames, ["field", "Krosno_3624", "Marki_4955",
                             "Przemysl_4581", "Warszawa_39512", "Legionowo_40593", "OSM"])
            rows = list(reader)
        self.assertEqual([row["field"] for row in rows], self.names)
        for row in rows:
            self.assertEqual(len(row), 7)
            self.assertTrue(all(isinstance(value, str) and value.strip() for value in row.values()))
            self.assertTrue(row["Warszawa_39512"].startswith("NIEPOTWIERDZONE"))


if __name__ == "__main__":
    unittest.main()
