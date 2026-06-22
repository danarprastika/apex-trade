"""Typed application settings loaded from environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.shared.constants import (
    DEFAULT_API_PREFIX,
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_ENV_FILE_ENCODING,
    DEFAULT_ENV_FILE_NAME,
    DEFAULT_HEALTH_ENDPOINT,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    DEFAULT_REDIS_MAX_CONNECTIONS,
    QUANTX_ENV_PREFIX,
)
from app.shared.enums import Environment
from app.shared.types import JsonDict


class ServerSettings(BaseModel):
    """Server binding and worker settings."""

    model_config = ConfigDict(extra="forbid")

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    workers: int = 1


class DatabaseSettings(BaseModel):
    """Database connection settings."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(default="postgresql+asyncpg://localhost:5432/quantx")
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0, le=100)
    echo: bool = False


class RedisSettings(BaseModel):
    """Redis connection settings."""

    model_config = ConfigDict(extra="forbid")

    url: str = "redis://localhost:6379/0"
    max_connections: int = Field(default=DEFAULT_REDIS_MAX_CONNECTIONS, ge=1)
    decode_responses: bool = True


class ApiSettings(BaseModel):
    """Public API settings."""

    model_config = ConfigDict(extra="forbid")

    prefix: str = DEFAULT_API_PREFIX
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    health_endpoint: str = DEFAULT_HEALTH_ENDPOINT


class LoggingSettings(BaseModel):
    """Logging settings."""

    model_config = ConfigDict(extra="forbid")

    level: str = DEFAULT_LOG_LEVEL
    format: str = "%(asctime)s %(name)s %(levelname)s %(message)s"
    file_path: Path | None = None


class SecuritySettings(BaseModel):
    """Security-related settings without owning authentication behavior."""

    model_config = ConfigDict(extra="forbid")

    secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=1440, ge=1)


class FeatureFlagSettings(BaseModel):
    """Feature flag settings for safe rollout control."""

    model_config = ConfigDict(extra="forbid")

    enable_websocket: bool = True
    enable_reporting: bool = True
    enable_advanced_analytics: bool = False
    enable_experimental_modules: bool = False


class ApplicationSettings(BaseSettings):
    """Root application settings.

    Settings are loaded from environment variables using the `QUANTX_` prefix.
    Nested settings can be overridden with double-underscore notation, for
    example `QUANTX_SERVER__PORT=8000`.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE_NAME,
        env_file_encoding=DEFAULT_ENV_FILE_ENCODING,
        env_nested_delimiter="__",
        env_prefix=QUANTX_ENV_PREFIX,
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = DEFAULT_APP_NAME
    app_version: str = DEFAULT_APP_VERSION
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    server: ServerSettings = ServerSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    api: ApiSettings = ApiSettings()
    logging: LoggingSettings = LoggingSettings()
    security: SecuritySettings = SecuritySettings()
    features: FeatureFlagSettings = FeatureFlagSettings()

    def to_safe_dict(self) -> JsonDict:
        """Return a sanitized settings dictionary safe for logs."""
        data = self.model_dump(mode="json")
        security = data.get("security")
        if isinstance(security, dict) and security.get("secret_key") is not None:
            security["secret_key"] = "***"
        return data


__all__ = [
    "ApiSettings",
    "ApplicationSettings",
    "DatabaseSettings",
    "FeatureFlagSettings",
    "LoggingSettings",
    "RedisSettings",
    "SecuritySettings",
    "ServerSettings",
]
