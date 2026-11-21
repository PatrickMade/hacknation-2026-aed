"""Access to the AED reference profile in aed-standard/ (validate.py and schema.json).

The wizard never copies validation rules: blocking errors come only from the
profile's own validate() function.
"""
import importlib.util
import json
import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path

from django.conf import settings


def standard_dir():
    return Path(settings.AED_STANDARD_DIR)


@lru_cache(maxsize=1)
def validator_module():
    path = standard_dir() / "validate.py"
    spec = importlib.util.spec_from_file_location("aed_standard_validate", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def schema():
    return json.loads((standard_dir() / "schema.json").read_text(encoding="utf-8"))


def fields():
    return schema()["fields"]


def field_names():
    return [field["name"] for field in fields()]


def required_names():
    return [field["name"] for field in fields() if field.get("constraints", {}).get("required")]


def version():
    return schema().get("x-version", "")


ROW_MESSAGE = re.compile(
    r"^wiersz (?P<line>\d+)(?:, (?P<field>[a-z_]+(?:\[\d+\](?:\.[a-z_]+)?)?(?:/[a-z_]+)?))?: (?P<message>.*)$"
)


def parse_message(text):
    """Split one validator message into CSV line, field and message for the report table."""
    match = ROW_MESSAGE.match(text)
    if not match:
        return {"line": None, "row": None, "field": "", "message": text}
    line = int(match.group("line"))
    return {"line": line, "row": line - 1, "field": match.group("field") or "", "message": match.group("message")}


def validate_bytes(data):
    """Run the profile validator on CSV bytes; nothing is kept after the call."""
    handle, path = tempfile.mkstemp(suffix=".csv", prefix="aed-check-")
    try:
        with os.fdopen(handle, "wb") as output:
            output.write(data)
        messages = validator_module().validate(path)
    finally:
        os.unlink(path)
    return [parse_message(message) for message in messages]
