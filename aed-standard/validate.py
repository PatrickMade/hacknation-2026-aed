#!/usr/bin/env python3
"""Local validator for the AED publication profile."""

import argparse
import csv
from datetime import date, datetime
import io
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

SCHEMA_PATH = Path(__file__).with_name("schema.json")
UTC_PATTERN = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"


def timestamp(value):
    if not re.fullmatch(UTC_PATTERN, value):
        raise ValueError("oczekiwano YYYY-MM-DDTHH:MM:SSZ (UTC)")
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def iso_date(value):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("oczekiwano YYYY-MM-DD")
    date.fromisoformat(value)


def web_url(value):
    url = urlsplit(value)
    if (url.scheme not in ("http", "https") or not url.hostname
            or url.username or url.password or re.search(r"\s", value)):
        raise ValueError("oczekiwano publicznego URL http(s) bez danych logowania")


def reject_constant(value):
    raise ValueError(f"niedozwolona stała JSON: {value}")


def scalar(value, field):
    """Check the Table Schema subset used by this profile, not arbitrary schemas."""
    constraints = field.get("constraints", {})
    if value == "":
        if constraints.get("required"):
            raise ValueError("wartość wymagana")
        return None
    if not value.strip():
        raise ValueError("same białe znaki nie są wartością")
    typ = field["type"]
    result = value
    if typ == "number":
        if not re.fullmatch(r"-?(?:[0-9]+)(?:\.[0-9]+)?", value):
            raise ValueError("oczekiwano liczby dziesiętnej z kropką")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("liczba musi być skończona")
        if "minimum" in constraints and result < constraints["minimum"]:
            raise ValueError(f"minimum: {constraints['minimum']}")
        if "maximum" in constraints and result > constraints["maximum"]:
            raise ValueError(f"maximum: {constraints['maximum']}")
        if "x-exclusiveMinimum" in field and result <= field["x-exclusiveMinimum"]:
            raise ValueError("liczba musi być większa od zera")
    elif typ == "boolean":
        if value not in ("true", "false"):
            raise ValueError("dozwolone: true, false lub puste pole")
        result = value == "true"
    elif typ == "date":
        iso_date(value)
    elif typ == "datetime":
        timestamp(value)
    elif typ == "array":
        result = json.loads(value, parse_constant=reject_constant)
        if not isinstance(result, list):
            raise ValueError("oczekiwano tablicy JSON")
    if "enum" in constraints and result not in constraints["enum"]:
        raise ValueError("dozwolone: " + ", ".join(constraints["enum"]))
    if "pattern" in constraints and not re.fullmatch(constraints["pattern"], value):
        raise ValueError("format niezgodny ze schematem")
    if "minLength" in constraints and len(result) < constraints["minLength"]:
        raise ValueError("wartość jest zbyt krótka")
    return result


REGON_WEIGHTS = {9: (8, 9, 2, 3, 4, 5, 6, 7), 14: (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)}


def regon_valid(value):
    """GUS check digit: weighted sum mod 11, where 10 counts as 0."""
    weights = REGON_WEIGHTS.get(len(value))
    if not weights or not value.isdigit():
        return False
    total = sum(int(digit) * weight for digit, weight in zip(value, weights))
    return total % 11 % 10 == int(value[-1])


def operator_rules(row, schema):
    """A report may keep a record with an unconfirmed operator only behind the placeholder and its flag;
    a dysponent's own publication must name the dysponent."""
    rule = schema["x-operatorUnconfirmed"]
    errors = []
    flags = row.get("quality_flags") if isinstance(row.get("quality_flags"), list) else []
    unconfirmed = rule["flag"] in flags
    if row.get("operator_name") == rule["placeholder"] and not unconfirmed:
        errors.append("operator_name: wartość \"{}\" wymaga flagi {}".format(rule["placeholder"], rule["flag"]))
    sources = row.get("source_records") if isinstance(row.get("source_records"), list) else []
    own = any(isinstance(s, dict) and str(s.get("source_id", "")).startswith(rule["forbiddenSourcePrefix"])
              for s in sources)
    if own and (unconfirmed or row.get("operator_name") == rule["placeholder"]):
        errors.append("operator_name: publikacja dysponenta musi wskazać potwierdzonego dysponenta")
    return errors


def record_rules(row, schema):
    errors = []
    lat, lon = row.get("latitude"), row.get("longitude")
    if (lat is None) != (lon is None):
        errors.append("latitude/longitude: wymagana para współrzędnych")
    if row.get("location_kind") == "fixed" and (lat is None or lon is None):
        errors.append("latitude/longitude: fixed wymaga obu współrzędnych")
    if lat is not None and lon is not None and not (48.9 <= lat <= 55.1 and 14 <= lon <= 24.2):
        errors.append("latitude/longitude: poza orientacyjną ramką Polski; sprawdź osie i źródło")
    if row.get("opening_hours") and not row.get("timezone"):
        errors.append("timezone: opening_hours wymaga strefy czasowej")
    if verified := row.get("last_verified_at"):
        try:
            iso_date(verified) if len(verified) == 10 else timestamp(verified)
        except ValueError as error:
            errors.append(f"last_verified_at: {error}")
    if regon := row.get("operator_regon"):
        if not regon_valid(regon):
            errors.append("operator_regon: niepoprawna cyfra kontrolna REGON")
    errors.extend(operator_rules(row, schema))
    if isinstance(row.get("quality_flags"), list):
        for flag in row["quality_flags"]:
            if not isinstance(flag, str) or flag not in schema["x-qualityFlags"]:
                errors.append("quality_flags: nieznana flaga jakości")
    if isinstance(row.get("source_records"), list):
        for index, source in enumerate(row["source_records"], 1):
            prefix = f"source_records[{index}]"
            if not isinstance(source, dict):
                errors.append(f"{prefix}: oczekiwano obiektu JSON")
                continue
            for key in schema["x-sourceRecord"]["required"]:
                if not isinstance(source.get(key), str) or not source[key].strip():
                    errors.append(f"{prefix}.{key}: wymagany niepusty tekst")
            for key in ("source_url", "license_url", "retrieved_at", "source_updated_at", "source_data_date"):
                if key not in source:
                    continue
                try:
                    if not isinstance(source[key], str) or not source[key]:
                        raise ValueError("oczekiwano niepustego tekstu")
                    if key.endswith("url"):
                        web_url(source[key])
                    elif key == "source_data_date":
                        iso_date(source[key])
                    else:
                        timestamp(source[key])
                except ValueError as error:
                    errors.append(f"{prefix}.{key}: {error}")
    return errors


def validate(path, template=False):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    fields = {field["name"]: field for field in schema["fields"]}
    errors = []
    try:
        raw = Path(path).read_bytes()
        text = raw.decode("utf-8")
        if "\n" in text.replace("\r\n", "") or "\r" in text.replace("\r\n", ""):
            errors.append("CSV: wymagane zakończenia wierszy CRLF")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, [])
        if not header or any(not name.strip() for name in header):
            return ["nagłówek: nazwy kolumn muszą być niepuste"]
        if len(header) != len(set(header)):
            return ["nagłówek: powtórzone nazwy kolumn"]
        unknown = set(header) - fields.keys()
        if unknown:
            return ["nagłówek: nieznane pola: " + ", ".join(sorted(unknown))]
        missing = [name for name, field in fields.items()
                   if field.get("constraints", {}).get("required") and name not in header]
        if missing:
            return ["nagłówek: brak wymaganych pól: " + ", ".join(missing)]
        if header != [name for name in fields if name in header]:
            errors.append("nagłówek: zachowaj kolejność pól ze schema.json")
        if template and header != list(fields):
            errors.append(f"szablon: wymagany pełny nagłówek {len(fields)} pól")
        records = 0
        used = set()
        ids = set()
        for row in reader:
            number = reader.line_num
            records += 1
            if template:
                errors.append(f"wiersz {number}: szablon nie może zawierać rekordów")
                break
            if len(row) != len(header):
                errors.append(f"wiersz {number}: liczba komórek {len(row)}, oczekiwano {len(header)}")
                continue
            parsed = {}
            for name, value in zip(header, row):
                if value != "":
                    used.add(name)
                try:
                    parsed[name] = scalar(value, fields[name])
                except (ValueError, TypeError) as error:
                    errors.append(f"wiersz {number}, {name}: {error}")
            errors.extend(f"wiersz {number}, {error}" for error in record_rules(parsed, schema))
            identity = parsed.get("aed_id")
            if identity:
                identity = identity.lower()
                if identity in ids:
                    errors.append(f"wiersz {number}, aed_id: powtórzony identyfikator")
                ids.add(identity)
        if not template:
            if not records:
                errors.append("CSV: brak rekordów; nagłówek sprawdź przez --template")
            elif empty := set(header) - used:
                errors.append("CSV: całkowicie puste kolumny: " + ", ".join(sorted(empty)))
    except (OSError, UnicodeError, csv.Error) as error:
        errors.append(f"CSV: {error}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", help="Plik CSV w profilu AED")
    parser.add_argument("--template", action="store_true", help="Sprawdź sam pełny nagłówek")
    args = parser.parse_args()
    errors = validate(args.csv_file, args.template)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("OK: " + ("szablon" if args.template else "dane") + " zgodne z kontrolami profilu AED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
