"""Application metadata model."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.configuration import ApplicationSettings


@dataclass(frozen=True, slots=True)
class AppMetadata:
    """Runtime application metadata."""

    app_name: str
    version: str
    environment: str
    python_version: str
    platform: str
    started_at: datetime

    @classmethod
    def from_settings(cls, settings: ApplicationSettings) -> AppMetadata:
        """Create metadata from application settings."""
        return cls(
            app_name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment.value,
            python_version=sys.version,
            platform=platform.platform(),
            started_at=datetime.now(UTC),
        )


def get_app_metadata(settings: ApplicationSettings) -> AppMetadata:
    """Return application metadata."""
    return AppMetadata.from_settings(settings)


__all__ = ["AppMetadata", "get_app_metadata"]
