"""Runtime environment enumeration."""

from __future__ import annotations

from enum import StrEnum


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def is_development(self) -> bool:
        """Return whether this environment is development."""
        return self is Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Return whether this environment is production."""
        return self is Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Return whether this environment is testing."""
        return self is Environment.TESTING


__all__ = ["Environment"]
