from __future__ import annotations

import json
from importlib import resources
from typing import Any

from jsonschema import Draft202012Validator


def _load_schema_text(name: str) -> str:
    return resources.files("teencare_ai.schemas").joinpath(name).read_text(encoding="utf-8")


def load_schema(name: str) -> dict[str, Any]:
    return json.loads(_load_schema_text(name))


def validate_json(instance: Any, schema_name: str) -> None:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        msg = "; ".join([f"{list(e.path)}: {e.message}" for e in errors[:5]])
        raise ValueError(f"Schema validation failed for {schema_name}: {msg}")

