"""Reusable utility functions."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def generate_id() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def slugify(value: str) -> str:
    """Convert a string to a URL-friendly slug."""
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value.strip("-")


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length with an optional suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def generate_nonce(length: int = 16) -> str:
    """Generate a fixed-length nonce string.

    Note: This uses a non-deterministic hash for uniqueness, not for security.
    """
    return hashlib.sha256(str(hash(object())).encode()).hexdigest()[:length]


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


__all__ = ["deep_merge", "generate_id", "generate_nonce", "slugify", "truncate", "utc_now"]
