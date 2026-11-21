"""Read a dysponent's source file (CSV, XLSX, GeoJSON) into columns and string rows."""
import csv
import datetime
import io
import ipaddress
import json
import socket
from urllib.parse import urljoin, urlsplit

import requests
import urllib3

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 20000
MAX_COLUMNS = 200
GEOJSON_LAT = "geometry_latitude"
GEOJSON_LON = "geometry_longitude"


class SourceError(ValueError):
    """A file or URL the wizard cannot read; the message is shown to the user."""


class Table:
    def __init__(self, columns, rows, kind):
        self.columns = columns
        self.rows = rows
        self.kind = kind

    def to_dict(self):
        return {"columns": self.columns, "rows": self.rows, "kind": self.kind}

    @classmethod
    def from_dict(cls, data):
        return cls(data["columns"], data["rows"], data["kind"])


def detect_kind(filename, data):
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xlsm")) or data[:2] == b"PK":
        return "xlsx"
    if name.endswith((".geojson", ".json")) or data.lstrip()[:1] in (b"{", b"["):
        return "geojson"
    return "csv"


def read(filename, data):
    if len(data) > MAX_BYTES:
        raise SourceError("Plik jest większy niż 10 MB.")
    if not data.strip():
        raise SourceError("Plik jest pusty.")
    kind = detect_kind(filename, data)
    table = {"csv": read_csv, "xlsx": read_xlsx, "geojson": read_geojson}[kind](data)
    if not table.columns:
        raise SourceError("Nie znaleziono nagłówka z nazwami kolumn.")
    if not table.rows:
        raise SourceError("Plik nie zawiera rekordów.")
    return table


def decode(data):
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise SourceError("Nie rozpoznano kodowania pliku (oczekiwano UTF-8 albo Windows-1250).")


def unique_columns(header):
    columns, seen = [], {}
    for index, name in enumerate(header, 1):
        name = (name or "").strip() or "kolumna_{}".format(index)
        if name in seen:
            seen[name] += 1
            name = "{} ({})".format(name, seen[name])
        else:
            seen[name] = 1
        columns.append(name)
    return columns


def rows_from(header, records):
    columns = unique_columns(header)
    rows = []
    for record in records:
        values = ["" if value is None else str(value).strip() for value in record]
        if not any(values):
            continue
        values += [""] * (len(columns) - len(values))
        rows.append(dict(zip(columns, values[:len(columns)])))
    return Table(columns, rows, "")


def read_csv(data):
    text = decode(data)
    try:
        delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    try:
        records = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    except csv.Error as error:
        raise SourceError("Błędny plik CSV: {}".format(error))
    if records and all(len(record) <= 1 for record in records):
        for inner in (",", ";"):
            if inner in records[0][0]:
                # Whole rows quoted as one cell (e.g. Marki): parse each cell again.
                lines = "\n".join(record[0] for record in records if record)
                records = list(csv.reader(io.StringIO(lines), delimiter=inner, skipinitialspace=True))
                break
    if not records:
        return Table([], [], "csv")
    table = rows_from(records[0], records[1:])
    table.kind = "csv"
    return table


def cell(value):
    if isinstance(value, datetime.datetime):
        return value.date().isoformat() if value.time() == datetime.time(0) else value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return value


def read_xlsx(data):
    from openpyxl import load_workbook

    try:
        sheet = load_workbook(io.BytesIO(data), read_only=True, data_only=True).worksheets[0]
    except Exception as error:  # openpyxl raises many types for damaged files
        raise SourceError("Nie można odczytać pliku XLSX: {}".format(error))
    records = []
    for row in sheet.iter_rows(max_col=MAX_COLUMNS, values_only=True):
        if len(records) > MAX_ROWS:
            raise SourceError("Arkusz ma więcej niż {} wierszy.".format(MAX_ROWS))
        records.append([cell(value) for value in row])
    while records and not any(value not in (None, "") for value in records[0]):
        records.pop(0)
    if not records:
        return Table([], [], "xlsx")
    table = rows_from(records[0], records[1:])
    table.kind = "xlsx"
    return table


def read_geojson(data):
    try:
        document = json.loads(decode(data))
    except ValueError as error:
        raise SourceError("Błędny plik GeoJSON: {}".format(error))
    features = document.get("features") if isinstance(document, dict) else None
    if not isinstance(features, list):
        raise SourceError("Oczekiwano GeoJSON FeatureCollection z listą features.")
    columns, rows = [], []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        row = {}
        for key, value in (feature.get("properties") or {}).items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            row[str(key)] = "" if value is None else str(value).strip()
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates")
        if geometry.get("type") == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
            row[GEOJSON_LON], row[GEOJSON_LAT] = str(coordinates[0]), str(coordinates[1])
        for key in row:
            if key not in columns:
                columns.append(key)
        rows.append(row)
    rows = [{column: row.get(column, "") for column in columns} for row in rows]
    return Table(columns, rows, "geojson")


def check_public_host(hostname):
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        raise SourceError("Nie można odnaleźć serwera z adresu URL.")
    for address in addresses:
        ip = ipaddress.ip_address(str(address).split("%")[0])
        if not ip.is_global:
            raise SourceError("Adres URL musi wskazywać publiczny serwer.")


MAX_REDIRECTS = 5


def checked_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise SourceError("Podaj publiczny adres http(s) bez danych logowania.")
    check_public_host(parts.hostname)
    return parts


def fetch(url):
    """Download a public file; every redirect hop is checked like the first URL."""
    parts = checked_url(url)
    try:
        for _ in range(MAX_REDIRECTS + 1):
            response = requests.get(url, timeout=20, stream=True, allow_redirects=False)
            if not response.is_redirect:
                break
            url = urljoin(url, response.headers["Location"])
            response.close()
            parts = checked_url(url)
        else:
            raise SourceError("Zbyt wiele przekierowań adresu URL.")
        try:
            if 300 <= response.status_code < 400:
                raise SourceError("Serwer zwrócił przekierowanie bez adresu docelowego.")
            response.raise_for_status()
            data = response.raw.read(MAX_BYTES + 1, decode_content=True)
        finally:
            response.close()
    except (requests.RequestException, urllib3.exceptions.HTTPError) as error:
        raise SourceError("Nie udało się pobrać pliku: {}".format(error))
    filename = parts.path.rsplit("/", 1)[-1]
    content_type = response.headers.get("Content-Type", "")
    if "spreadsheetml" in content_type and not filename.lower().endswith(".xlsx"):
        filename += ".xlsx"
    return filename, data
