"""Base entity foundation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


def _utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


@dataclass
class BaseEntity:
    """Base class for domain entities with auto-generated identifiers and timestamps."""

    id: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize auto-generated fields after dataclass construction."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = _utc_now()
        if self.updated_at is None:
            self.updated_at = _utc_now()

    def touch(self) -> None:
        """Update the modification timestamp to the current UTC time."""
        self.updated_at = _utc_now()


__all__ = ["BaseEntity"]
