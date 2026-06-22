"""Dependency scope values."""

from __future__ import annotations

from enum import StrEnum


class DependencyScope(StrEnum):
    """Dependency lifetime scope."""

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


__all__ = ["DependencyScope"]
