"""Sensitive data sanitization for logs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.shared.types import JsonValue

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "password",
        "private_key",
        "secret",
        "set-cookie",
        "token",
    }
)


def is_sensitive_key(key: str) -> bool:
    """Return whether a key should be redacted."""
    normalized = key.lower()
    return any(sensitive in normalized for sensitive in SENSITIVE_KEYS)


def mask_secret(value: str | None, *, visible_chars: int = 4) -> str | None:
    """Mask a secret while preserving a small suffix for diagnostics."""
    if value is None:
        return None
    if len(value) <= visible_chars:
        return "*" * len(value)
    return f"{'*' * (len(value) - visible_chars)}{value[-visible_chars:]}"


def sanitize_for_logging(value: object) -> JsonValue:
    """Recursively sanitize a value for logging."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        sanitized: dict[str, JsonValue] = {}
        for key, item in value.items():
            key_text = str(key)
            sanitized[key_text] = (
                "***" if is_sensitive_key(key_text) else sanitize_for_logging(item)
            )
        return sanitized
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [sanitize_for_logging(item) for item in value]
    return str(value)


__all__ = ["SENSITIVE_KEYS", "is_sensitive_key", "mask_secret", "sanitize_for_logging"]
