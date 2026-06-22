"""Error severity enumeration."""

from __future__ import annotations

from enum import StrEnum


class ErrorSeverity(StrEnum):
    """Operational error severity values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


__all__ = ["ErrorSeverity"]
