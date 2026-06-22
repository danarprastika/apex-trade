"""Masking helpers."""

from __future__ import annotations

from collections.abc import Mapping

from app.shared.types import JsonValue


def redact_sensitive_keys(value: Mapping[str, object], *, replacement: str = "***") -> JsonValue:
    """Redact sensitive keys from a mapping."""
    result: dict[str, JsonValue] = {}
    for key, item in value.items():
        if _is_sensitive(str(key)):
            result[key] = replacement
        elif isinstance(item, Mapping):
            result[key] = redact_sensitive_keys(item, replacement=replacement)
        elif isinstance(item, list):
            result[key] = [_to_jsonable(entry) for entry in item]
        else:
            result[key] = _to_jsonable(item)
    return result


def _to_jsonable(value: object) -> JsonValue:
    """Convert a scalar value to a JSON-compatible value."""
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _is_sensitive(key: str) -> bool:
    """Return whether a key is sensitive."""
    normalized = key.lower()
    sensitive_parts = ("secret", "token", "password", "api_key", "private_key", "authorization")
    return any(part in normalized for part in sensitive_parts)


__all__ = ["redact_sensitive_keys"]
