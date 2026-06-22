"""Settings validation helpers."""

from __future__ import annotations

from urllib.parse import urlparse

from app.core.exceptions.configuration import SettingsValidationError
from app.shared.enums import Environment

from .settings import ApplicationSettings


def validate_settings(settings: ApplicationSettings) -> None:
    """Validate application settings after environment loading."""
    _validate_environment(settings)
    _validate_server(settings)
    _validate_database(settings)
    _validate_api(settings)
    _validate_logging(settings)
    _validate_security(settings)


def _validate_environment(settings: ApplicationSettings) -> None:
    """Validate environment-specific rules."""
    if settings.environment is Environment.PRODUCTION and settings.debug:
        raise SettingsValidationError(
            message="Debug mode must be disabled in production",
            code="INVALID_PRODUCTION_DEBUG",
            details={"environment": settings.environment.value, "debug": settings.debug},
            user_message="Production configuration is invalid.",
        )


def _validate_server(settings: ApplicationSettings) -> None:
    """Validate server settings."""
    if not 1 <= settings.server.port <= 65535:
        raise SettingsValidationError(
            message="Server port must be between 1 and 65535",
            code="INVALID_SERVER_PORT",
            details={"port": settings.server.port},
        )
    if settings.server.workers < 1:
        raise SettingsValidationError(
            message="Server workers must be at least 1",
            code="INVALID_SERVER_WORKERS",
            details={"workers": settings.server.workers},
        )


def _validate_database(settings: ApplicationSettings) -> None:
    """Validate database settings."""
    if settings.environment is Environment.PRODUCTION:
        parsed = urlparse(settings.database.url)
        if parsed.scheme != "postgresql+asyncpg":
            raise SettingsValidationError(
                message="Production database URL must use postgresql+asyncpg",
                code="INVALID_DATABASE_URL",
                details={"scheme": parsed.scheme},
                user_message="Database configuration is invalid.",
            )


def _validate_api(settings: ApplicationSettings) -> None:
    """Validate API settings."""
    if not settings.api.prefix.startswith("/"):
        raise SettingsValidationError(
            message="API prefix must start with '/'",
            code="INVALID_API_PREFIX",
            details={"prefix": settings.api.prefix},
        )
    if not settings.api.docs_url.startswith("/"):
        raise SettingsValidationError(
            message="Docs URL must start with '/'",
            code="INVALID_DOCS_URL",
            details={"docs_url": settings.api.docs_url},
        )
    if not settings.api.redoc_url.startswith("/"):
        raise SettingsValidationError(
            message="ReDoc URL must start with '/'",
            code="INVALID_REDOC_URL",
            details={"redoc_url": settings.api.redoc_url},
        )


def _validate_logging(settings: ApplicationSettings) -> None:
    """Validate logging settings."""
    if settings.logging.level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise SettingsValidationError(
            message="Invalid logging level",
            code="INVALID_LOG_LEVEL",
            details={"log_level": settings.logging.level},
        )


def _validate_security(settings: ApplicationSettings) -> None:
    """Validate security settings."""
    if settings.environment is Environment.PRODUCTION and settings.security.secret_key is None:
        raise SettingsValidationError(
            message="Production requires a secret key",
            code="MISSING_SECRET_KEY",
            user_message="Security configuration is invalid.",
        )


__all__ = ["validate_settings"]
