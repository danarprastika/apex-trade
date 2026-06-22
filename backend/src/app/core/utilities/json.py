"""JSON serialization helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum

from app.shared.types import JsonValue


def to_jsonable(value: object) -> JsonValue:
    """Convert a value to a JSON-compatible value."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return to_jsonable(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [to_jsonable(item) for item in value]
    return str(value)


def json_dumps(value: JsonValue) -> str:
    """Serialize JSON-compatible data."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_loads(value: str) -> JsonValue:
    """Deserialize JSON-compatible data."""
    loaded = json.loads(value)
    return to_jsonable(loaded)


__all__ = ["json_dumps", "json_loads", "to_jsonable"]
