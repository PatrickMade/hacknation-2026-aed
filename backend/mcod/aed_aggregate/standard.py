"""Access to the AED profile in aed-standard/ (schema.json, validate.py), never a copy of its rules."""
import csv
import importlib.util
import io
import json
from pathlib import Path

# Repository root in a checkout (backend/mcod/aed_aggregate -> ../../..) and
# /usr/src in the container, where compose mounts aed-standard/ read-only.
STANDARD_DIR = Path(__file__).resolve().parents[3] / 'aed-standard'


def _load_validator():
    path = STANDARD_DIR / 'validate.py'
    spec = importlib.util.spec_from_file_location('aed_standard_validate', str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_validator()
SCHEMA = json.loads((STANDARD_DIR / 'schema.json').read_text(encoding='utf-8'))
FIELDS = [field['name'] for field in SCHEMA['fields']]
FIELD_DEFS = {field['name']: field for field in SCHEMA['fields']}
MAP_COLUMNS = SCHEMA['x-map']  # {"latitude": "b", "longitude": "l", "name": "label"}


def cell(value):
    """Serialise one record value to the profile's CSV text form."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    if isinstance(value, float):
        return repr(value)
    return str(value)


def record_errors(record):
    """Per-record check with validate.py's field and record rules."""
    errors, parsed = [], {}
    for name in FIELDS:
        try:
            parsed[name] = validator.scalar(cell(record.get(name)), FIELD_DEFS[name])
        except (ValueError, TypeError) as error:
            errors.append('{}: {}'.format(name, error))
    errors.extend(validator.record_rules(parsed, SCHEMA))
    return errors


def to_csv(records):
    """CSV in schema order with CRLF; columns empty in every record are left out (validate.py rejects them)."""
    used = [name for name in FIELDS if any(cell(r.get(name)) != '' for r in records)]
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\r\n')
    writer.writerow(used)
    for record in records:
        writer.writerow([cell(record.get(name)) for name in used])
    return buffer.getvalue().encode('utf-8'), used


def file_errors(path):
    return validator.validate(str(path))
