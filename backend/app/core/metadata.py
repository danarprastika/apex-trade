"""Application metadata for the QuantX AI core package."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import cast

from pydantic import BaseModel, ConfigDict, Field

from .constants import DEFAULT_APP_NAME, DEFAULT_APP_VERSION, PYTHON_VERSION, SEMVER_PATTERN
from .enums import Environment
from .settings import CoreSettings

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class ApplicationMetadata(BaseModel):
    """Immutable application identity and runtime metadata."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    name: str = Field(default=DEFAULT_APP_NAME, min_length=1, max_length=80)
    version: str = Field(default=DEFAULT_APP_VERSION, pattern=SEMVER_PATTERN)
    environment: Environment
    build: str | None = Field(default=None, min_length=1, max_length=128)
    started_at: datetime = Field(default_factory=utc_now)
    python_version: str = Field(default=PYTHON_VERSION, min_length=1)
    api_version: str = Field(default="v1", pattern=r"^v\d+$")

    @classmethod
    def from_settings(cls, settings: CoreSettings) -> ApplicationMetadata:
        """Create metadata from validated core settings."""
        return cls(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

    def to_dict(self) -> JsonDict:
        """Convert metadata to a JSON-serializable dictionary."""
        return cast(JsonDict, self.model_dump(mode="json"))

    @property
    def is_production(self) -> bool:
        """Return whether the application is running in production."""
        return self.environment is Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Return whether the application is running in development."""
        return self.environment is Environment.DEVELOPMENT


__all__ = ["ApplicationMetadata", "utc_now"]
