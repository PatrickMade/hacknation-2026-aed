"""Map a source table to the AED profile columns and produce a profile CSV.

Only conversion and non-blocking diagnostics live here. Whether the result is
compliant is decided by aed-standard/validate.py (see standard.validate_bytes).
"""
import csv
import datetime
import io
import json
import re
import unicodedata
import uuid

from mcod.aed_wizard import standard

ADDRESS = "_address"
SOURCE_ID = "_source_id"

# Normalized source header names recognized for each target (first match wins).
ALIASES = {
    "aed_id": ["aed_id", "uuid"],
    SOURCE_ID: ["id", "lp", "l_p", "numer_id", "identyfikator", "nr_ewidencyjny", "numer_ewidencyjny",
                "objectid", "fid", "source_record_id"],
    "name": ["name", "nazwa_punktu", "lokalizacja", "nazwa", "nazwa_obiektu", "obiekt", "miejsce"],
    "latitude": ["latitude", "szerokosc_geograficzna", "szerokosc", "lat", "wspolrzedna_y", "y",
                 "geometry_latitude"],
    "longitude": ["longitude", "dlugosc_geograficzna", "dlugosc", "lon", "lng", "long", "wspolrzedna_x", "x",
                  "geometry_longitude"],
    "simc": ["simc", "kod_simc"],
    "locality": ["locality", "miejscowosc", "miasto", "city"],
    "street_type": ["street_type", "cecha_ulicy", "cecha"],
    "street": ["street", "ulica", "nazwa_ulicy", "ul"],
    "house_number": ["house_number", "home_number", "nr_budynku", "numer_budynku", "numer_domu", "nr_domu"],
    "unit_number": ["unit_number", "nr_lokalu", "numer_lokalu"],
    "postcode": ["postcode", "kod_pocztowy"],
    ADDRESS: ["adres", "address"],
    "location_description": ["location_description", "opis_lokalizacji", "umiejscowienie", "dokladna_lokalizacja",
                             "opis_miejsca", "opis"],
    "indoor": ["indoor", "wewnatrz", "w_budynku"],
    "level": ["level", "pietro", "kondygnacja"],
    "access": ["access", "dostep"],
    "opening_hours": ["opening_hours", "godziny_dostepnosci", "godziny_otwarcia", "godziny", "dostepnosc"],
    "opening_hours_raw": ["opening_hours_raw"],
    "access_notes": ["access_notes", "uwagi", "informacje_dodatkowe"],
    "operator_name": ["operator_name", "dysponent", "wlasciciel", "operator"],
    "public_phone": ["public_phone", "phone", "telefon", "tel", "nr_telefonu"],
    "public_email": ["public_email", "email", "e_mail", "adres_email"],
    "manufacturer": ["manufacturer", "producent"],
    "model": ["model"],
}

# Defaults the dysponent confirms in the wizard for required fields without a source column.
DEFAULTS = {
    "location_kind": "fixed",
    "coordinate_method": "source",
    "indoor": "unknown",
    "access": "unknown",
    "locked": "unknown",
    "operational_status": "unknown",
    "verification_method": "unknown",
}
GENERATED = ("country_code", "timezone", "source_records", "retrieved_at", "updated_at", "quality_flags")
POLAND = (48.9, 55.1, 14.0, 24.2)  # Same orientation box as validate.py; used only to suggest an axis swap.

YES = {"tak", "t", "yes", "y", "1", "true", "prawda"}
NO = {"nie", "n", "no", "0", "false", "falsz"}
ENUM_WORDS = {
    "location_kind": {"stacjonarny": "fixed", "staly": "fixed", "mobilny": "mobile", "przenosny": "mobile"},
    "access": {"publiczny": "public", "publiczne": "public", "ogolnodostepny": "public",
               "ogolnodostepne": "public", "dla_klientow": "customers", "prywatny": "private",
               "ograniczony": "restricted"},
    "operational_status": {"sprawny": "working", "dziala": "working", "niesprawny": "out_of_service",
                           "wycofany": "removed"},
}
ALWAYS_HOURS = {"24/7", "24h", "24_h", "calodobowo", "cala_doba", "cala_dobe", "przez_cala_dobe", "24_7",
                "cala_dobe_7_dni_w_tygodniu"}
OSM_HOURS = re.compile(
    r"^(24/7|((Mo|Tu|We|Th|Fr|Sa|Su|PH|SH)(-(Mo|Tu|We|Th|Fr|Sa|Su))?(,(Mo|Tu|We|Th|Fr|Sa|Su|PH)(-(Mo|Tu|We|Th|Fr|Sa|Su))?)*"
    r"( (\d\d:\d\d-\d\d:\d\d(,\d\d:\d\d-\d\d:\d\d)*|off|closed))?)(; ?((Mo|Tu|We|Th|Fr|Sa|Su|PH|SH)"
    r"(-(Mo|Tu|We|Th|Fr|Sa|Su))?(,(Mo|Tu|We|Th|Fr|Sa|Su|PH)(-(Mo|Tu|We|Th|Fr|Sa|Su))?)*( (\d\d:\d\d-\d\d:\d\d"
    r"(,\d\d:\d\d-\d\d:\d\d)*|off|closed))?))*|\d\d:\d\d-\d\d:\d\d)$"
)
ADDRESS_PATTERN = re.compile(
    r"^(?:(?P<type>ul|al|pl|os|ulica|aleja|plac|osiedle)\.*\s+)?(?P<street>[^,]*?)"
    r"(?:\s+(?P<number>\d+[A-Za-z]?(?:/\d+[A-Za-z]?)?))?\s*,\s*(?P<postcode>\d{2}-\d{3})\s+(?P<locality>.+)$",
    re.IGNORECASE,
)
STREET_TYPES = {"ul": "ulica", "ulica": "ulica", "al": "aleja", "aleja": "aleja", "pl": "plac", "plac": "plac",
                "os": "osiedle", "osiedle": "osiedle"}
UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text).replace("ł", "l").replace("Ł", "L"))
    text = "".join(char for char in text if not unicodedata.combining(char)).lower()
    return re.sub(r"[^a-z0-9/]+", "_", text).strip("_")


def targets():
    """Targets offered in the mapping form: source id, profile fields and the split address."""
    titles = {field["name"]: field.get("title", field["name"]) for field in standard.fields()}
    options = [(SOURCE_ID, "Identyfikator rekordu w źródle (source_record_id)")]
    for name in standard.field_names():
        if name not in GENERATED:
            options.append((name, "{} ({})".format(titles[name], name)))
    options.append((ADDRESS, "Adres w jednej kolumnie (ulica numer, kod miejscowość)"))
    return options


DATE_ORIGINS = ("source_records.source_data_date", "updated_at", "retrieved_at")


def iso_day(value):
    """YYYY-MM-DD of a profile date or UTC timestamp; None for anything else."""
    value = (value or "").strip() if isinstance(value, str) else ""
    if len(value) < 10 or (len(value) > 10 and value[10] != "T"):
        return None
    try:
        return datetime.date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def detect_data_date(table):
    """The day the data describe, read from profile columns of the source file (APP-61).

    Order: latest source_records[].source_data_date, then latest updated_at, then latest retrieved_at.
    Returns (YYYY-MM-DD, origin) or (None, None) when the file carries no such date.
    """
    found = {origin: set() for origin in DATE_ORIGINS}
    for row in table.rows:
        try:
            items = json.loads(row.get("source_records") or "[]")
        except ValueError:
            items = []
        for item in items if isinstance(items, list) else []:
            day = iso_day(item.get("source_data_date")) if isinstance(item, dict) else None
            if day:
                found["source_records.source_data_date"].add(day)
        for field in ("updated_at", "retrieved_at"):
            day = iso_day(row.get(field))
            if day:
                found[field].add(day)
    for origin in DATE_ORIGINS:
        if found[origin]:
            return max(found[origin]), origin
    return None, None


def suggest(columns):
    """Guess a source column for each target by profile name, Polish title or alias."""
    by_key = {}
    for column in columns:
        by_key.setdefault(normalize(column), column)
    titles = {field["name"]: normalize(field.get("title", "")) for field in standard.fields()}
    used, mapping = set(), {}
    for target, _ in targets():
        candidates = [target] + ([titles[target]] if target in titles else []) + ALIASES.get(target, [])
        for candidate in candidates:
            column = by_key.get(candidate)
            if column and column not in used:
                mapping[target] = column
                used.add(column)
                break
    if ADDRESS in mapping and any(key in mapping for key in ("street", "postcode", "locality")):
        del mapping[ADDRESS]
    return mapping


def number(value):
    value = value.replace(" ", "").replace(",", ".")
    return value[:-1] if value.endswith("°") else value


def parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def in_poland(lat, lon):
    return POLAND[0] <= lat <= POLAND[1] and POLAND[2] <= lon <= POLAND[3]


def clean_value(field, value):
    value = value.strip()
    if not value:
        return value
    key = normalize(value)
    if field in ("latitude", "longitude", "coordinate_accuracy_m"):
        return number(value)
    if field in ("indoor", "locked"):
        return "yes" if key in YES else "no" if key in NO else value
    if field == "pediatric_pads":
        return "true" if key in YES else "false" if key in NO else value
    if field in ENUM_WORDS:
        return ENUM_WORDS[field].get(key, value)
    if field == "public_phone":
        digits = re.sub(r"[\s\-()]", "", value)
        if re.fullmatch(r"\d{9}", digits):
            return "+48" + digits
        if re.fullmatch(r"(00)?48\d{9}", digits):
            return "+" + digits[-11:]
        return digits
    if field == "postcode" and re.fullmatch(r"\d{5}", value):
        return value[:2] + "-" + value[2:]
    if field in ("last_maintenance_on", "pads_expire_on", "battery_expires_on"):
        match = re.fullmatch(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", value)
        if match:
            return "{}-{:02d}-{:02d}".format(match.group(3), int(match.group(2)), int(match.group(1)))
    return re.sub(r"\s+", " ", value)


def split_address(value):
    match = ADDRESS_PATTERN.match(value.strip())
    if not match or not match.group("street").strip():
        return {}
    parts = {
        "street": match.group("street").strip(),
        "postcode": match.group("postcode"),
        "locality": match.group("locality").strip(),
    }
    if match.group("type"):
        parts["street_type"] = STREET_TYPES[match.group("type").lower()]
    if match.group("number"):
        parts["house_number"] = match.group("number")
    return parts


class Conversion:
    def __init__(self, columns, records, warnings, generated_ids):
        self.columns = columns
        self.records = records
        self.warnings = warnings
        self.generated_ids = generated_ids

    def csv_bytes(self):
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(self.columns)
        for record in self.records:
            writer.writerow([record.get(column, "") for column in self.columns])
        return output.getvalue().encode("utf-8")


def convert(table, mapping, defaults, context, swap_axes=False):
    """Build profile records.

    mapping: target -> source column; defaults: field -> constant for empty values;
    context: org_slug, operator_name, source_url, license_url, data_date, now (UTC text).
    """
    warnings, generated_ids, records = [], 0, []
    flags_by_row = {}
    seen_points, seen_addresses = {}, {}
    source_id = "dysponent:" + context["org_slug"]
    for index, row in enumerate(table.rows, 1):
        record, flags = {}, []
        for target, column in mapping.items():
            if column and column in row and target not in (SOURCE_ID, ADDRESS):
                record[target] = clean_value(target, row[column])
        if mapping.get(ADDRESS):
            address = row.get(mapping[ADDRESS], "")
            parts = split_address(address)
            if parts:
                for key, value in parts.items():
                    if not record.get(key):
                        record[key] = value
            elif address and not record.get("location_description"):
                record["location_description"] = address
        for field, value in defaults.items():
            if value and not record.get(field):
                record[field] = value
        if not record.get("operator_name"):
            record["operator_name"] = context["operator_name"]
        record["country_code"] = "PL"

        hours = record.get("opening_hours", "")
        if hours:
            if normalize(hours) in ALWAYS_HOURS:
                record["opening_hours"] = "24/7"
            elif not OSM_HOURS.match(hours):
                record["opening_hours"] = ""
                if not record.get("opening_hours_raw"):
                    record["opening_hours_raw"] = hours
                flags.append("ambiguous_hours")
                warnings.append(warning(index, "opening_hours", "Godziny nie są w składni OSM opening_hours; "
                                                                "zapisano je w opening_hours_raw."))
        if record.get("opening_hours"):
            record["timezone"] = "Europe/Warsaw"

        lat, lon = parse_float(record.get("latitude")), parse_float(record.get("longitude"))
        if lat is not None and lon is not None and not in_poland(lat, lon):
            if in_poland(lon, lat):
                flags.append("suspected_axis_swap")
                if swap_axes:
                    record["latitude"], record["longitude"] = record["longitude"], record["latitude"]
                    lat, lon = lon, lat
                    message = "Zamieniono szerokość i długość geograficzną (oznaczenie suspected_axis_swap)."
                else:
                    message = "Prawdopodobnie zamienione osie: po zamianie punkt leży w Polsce."
                warnings.append(warning(index, "latitude/longitude", message))
            else:
                flags.append("outside_expected_area")

        record_id = row.get(mapping.get(SOURCE_ID, ""), "").strip()
        given = record.get("aed_id", "")
        if not UUID_PATTERN.match(given):
            record_id = record_id or given or "wiersz-{}".format(index)
            record["aed_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "aed:{}:{}".format(source_id, record_id)))
            generated_ids += 1
        record_id = record_id or record["aed_id"]

        if lat is not None and lon is not None:
            point = (round(lat, 5), round(lon, 5))
            if point in seen_points:
                duplicate(index, seen_points[point], "te same współrzędne", flags, flags_by_row, warnings)
            else:
                seen_points[point] = index
        address_key = normalize(" ".join(record.get(key, "") for key in ("name", "street", "house_number", "locality")))
        if record.get("street") and address_key:
            if address_key in seen_addresses:
                duplicate(index, seen_addresses[address_key], "ta sama nazwa i adres", flags, flags_by_row, warnings)
            else:
                seen_addresses[address_key] = index

        source = {
            "source_id": source_id,
            "source_record_id": record_id,
            "source_url": context["source_url"],
            "retrieved_at": context["now"],
            "license_url": context["license_url"],
        }
        if context.get("data_date"):
            source["source_data_date"] = context["data_date"]
        record["source_records"] = json.dumps([source], ensure_ascii=False, separators=(",", ":"))
        record["retrieved_at"] = context["now"]
        record["updated_at"] = context["now"]
        flags_by_row[index] = flags
        records.append(record)

    for index, record in enumerate(records, 1):
        flags = sorted(set(flags_by_row[index]))
        record["quality_flags"] = json.dumps(flags)
    names = standard.field_names()
    required = set(standard.required_names())
    columns = [name for name in names if name in required or any(record.get(name) for record in records)]
    return Conversion(columns, records, warnings, generated_ids)


def warning(row, field, message):
    return {"row": row, "line": row + 1, "field": field, "message": message}


def duplicate(index, first, reason, flags, flags_by_row, warnings):
    flags.append("duplicate_candidate")
    flags_by_row[first].append("duplicate_candidate")
    warnings.append(warning(index, "", "Możliwy duplikat rekordu {} ({}).".format(first, reason)))
