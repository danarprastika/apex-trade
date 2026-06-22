"""Pydantic settings for the QuantX AI core package.

Core settings are loaded from environment variables with the `QUANTX_` prefix
and validated during application bootstrap. The settings model intentionally
contains only process-level concerns so domain, infrastructure, and
presentation layers receive typed configuration through dependency injection.
"""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import (
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_DETAILED_HEALTH_PATH,
    DEFAULT_ENVIRONMENT,
    DEFAULT_HEALTH_PATH,
    DEFAULT_HOST,
    DEFAULT_LIVENESS_PATH,
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    DEFAULT_READINESS_PATH,
    DEFAULT_SENSITIVE_FIELD_NAMES,
    DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
    DEFAULT_STARTUP_TIMEOUT_SECONDS,
    DEFAULT_WORKERS,
    ENV_FILE,
    ENV_PREFIX,
    SEMVER_PATTERN,
)
from .enums import Environment, LogFormat, LogLevel
from .exceptions import SettingsValidationError


class CoreSettings(BaseSettings):
    """Validated configuration for core package behavior."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_prefix=ENV_PREFIX,
        extra="ignore",
        frozen=True,
        str_strip_whitespace=True,
    )

    app_name: str = Field(default=DEFAULT_APP_NAME, min_length=1, max_length=80)
    app_version: str = Field(default=DEFAULT_APP_VERSION, pattern=SEMVER_PATTERN)
    environment: Environment = DEFAULT_ENVIRONMENT
    log_level: LogLevel = DEFAULT_LOG_LEVEL
    log_format: LogFormat = DEFAULT_LOG_FORMAT
    debug: bool = False

    host: str = Field(default=DEFAULT_HOST, min_length=1, max_length=255)
    port: int = Field(default=DEFAULT_PORT, ge=1, le=65535)
    workers: int = Field(default=DEFAULT_WORKERS, ge=1, le=64)

    correlation_id_header: str = Field(default="X-Correlation-ID", min_length=1, max_length=128)
    health_path: str = Field(default=DEFAULT_HEALTH_PATH, min_length=2, max_length=2048)
    liveness_path: str = Field(default=DEFAULT_LIVENESS_PATH, min_length=2, max_length=2048)
    readiness_path: str = Field(default=DEFAULT_READINESS_PATH, min_length=2, max_length=2048)
    detailed_health_path: str = Field(
        default=DEFAULT_DETAILED_HEALTH_PATH,
        min_length=2,
        max_length=2048,
    )

    startup_timeout_seconds: float = Field(default=DEFAULT_STARTUP_TIMEOUT_SECONDS, gt=0)
    shutdown_timeout_seconds: float = Field(default=DEFAULT_SHUTDOWN_TIMEOUT_SECONDS, gt=0)
    log_sensitive_field_names: tuple[str, ...] = Field(
        default_factory=lambda: tuple(sorted(DEFAULT_SENSITIVE_FIELD_NAMES))
    )

    @field_validator("app_name", "host", "correlation_id_header")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """Normalize non-empty text fields."""
        normalized = value.strip()
        if not normalized:
            raise SettingsValidationError("Field must not be empty")
        return normalized

    @field_validator("health_path", "liveness_path", "readiness_path", "detailed_health_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Normalize HTTP health paths."""
        normalized = value.strip()
        if not normalized.startswith("/"):
            raise SettingsValidationError("Health path must start with '/'")
        if any(character.isspace() for character in normalized):
            raise SettingsValidationError("Health path must not contain whitespace")
        return normalized

    @field_validator("environment")
    @classmethod
    def parse_environment(cls, value: object) -> Environment:
        """Parse environment values case-insensitively."""
        if isinstance(value, Environment):
            return value
        try:
            return Environment(str(value).strip().lower())
        except ValueError as exc:
            raise SettingsValidationError(f"Invalid environment: {value}") from exc

    @field_validator("log_level")
    @classmethod
    def parse_log_level(cls, value: object) -> LogLevel:
        """Parse log level values case-insensitively."""
        if isinstance(value, LogLevel):
            return value
        try:
            return LogLevel(str(value).strip().lower())
        except ValueError as exc:
            raise SettingsValidationError(f"Invalid log level: {value}") from exc

    @field_validator("log_format")
    @classmethod
    def parse_log_format(cls, value: object) -> LogFormat:
        """Parse log format values case-insensitively."""
        if isinstance(value, LogFormat):
            return value
        try:
            return LogFormat(str(value).strip().lower())
        except ValueError as exc:
            raise SettingsValidationError(f"Invalid log format: {value}") from exc

    @field_validator("log_sensitive_field_names")
    @classmethod
    def normalize_sensitive_fields(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Normalize sensitive log field names."""
        normalized = {field.strip().lower() for field in value if field.strip()}
        return tuple(sorted(normalized))

    @model_validator(mode="after")
    def validate_runtime_constraints(self) -> CoreSettings:
        """Validate cross-field runtime constraints."""
        if self.environment is Environment.PRODUCTION and self.debug:
            raise SettingsValidationError("Debug mode must be disabled in production")

        health_paths = {
            self.health_path,
            self.liveness_path,
            self.readiness_path,
            self.detailed_health_path,
        }
        if len(health_paths) != 4:
            raise SettingsValidationError("Health check paths must be unique")

        return self


def load_settings() -> CoreSettings:
    """Load and validate core settings from environment variables."""
    return CoreSettings()


__all__ = ["CoreSettings", "load_settings"]
