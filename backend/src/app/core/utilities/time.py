"""Time helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def format_timestamp(value: datetime) -> str:
    """Format a timestamp in UTC ISO-8601 format."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp."""
    return datetime.fromisoformat(value)


__all__ = ["format_timestamp", "parse_timestamp", "utc_now"]
