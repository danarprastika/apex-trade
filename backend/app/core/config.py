"""Core configuration assembly for QuantX AI."""

from __future__ import annotations

from dataclasses import dataclass
from logging import Logger as StdlibLogger

from .exceptions import ConfigurationError
from .logging import configure_logging, get_logger
from .metadata import ApplicationMetadata
from .settings import CoreSettings, load_settings


@dataclass(frozen=True, slots=True)
class CoreConfig:
    """Immutable runtime configuration for core services."""

    settings: CoreSettings
    metadata: ApplicationMetadata
    logger: StdlibLogger

    @property
    def app_name(self) -> str:
        """Return the configured application name."""
        return self.settings.app_name

    @property
    def app_version(self) -> str:
        """Return the configured application version."""
        return self.settings.app_version

    def to_dict(self) -> dict[str, object]:
        """Return a redacted configuration summary."""
        return {
            "settings": self.settings.model_dump(mode="json"),
            "metadata": self.metadata.to_dict(),
        }


def validate_core_settings(settings: CoreSettings) -> None:
    """Validate runtime constraints that are safer outside Pydantic."""
    if settings.environment.value == "production" and settings.debug:
        raise ConfigurationError(
            message="Debug mode must be disabled in production",
            code="PRODUCTION_DEBUG_ENABLED",
            user_message="Production configuration rejected debug mode",
        )

    if settings.startup_timeout_seconds <= 0:
        raise ConfigurationError(message="Startup timeout must be positive")
    if settings.shutdown_timeout_seconds <= 0:
        raise ConfigurationError(message="Shutdown timeout must be positive")


def create_core_config(
    settings: CoreSettings | None = None,
    *,
    configure_logger: bool = True,
) -> CoreConfig:
    """Create validated core configuration and optional logging setup."""
    resolved_settings = settings or load_settings()
    validate_core_settings(resolved_settings)
    metadata = ApplicationMetadata.from_settings(resolved_settings)
    logger = configure_logging(resolved_settings) if configure_logger else get_logger()
    return CoreConfig(settings=resolved_settings, metadata=metadata, logger=logger)


def load_core_config(
    settings: CoreSettings | None = None,
    *,
    configure_logger: bool = True,
) -> CoreConfig:
    """Load core configuration from validated settings."""
    return create_core_config(settings=settings, configure_logger=configure_logger)


__all__ = ["CoreConfig", "create_core_config", "load_core_config", "validate_core_settings"]
