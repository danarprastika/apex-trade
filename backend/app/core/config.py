import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "APEX"
    app_env: str = "development"
    debug: bool = True
    create_tables_on_startup: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_user: str = "apex"
    postgres_password: str = "apex_password"
    postgres_db: str = "apex_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret_key: str = "CHANGE_THIS_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    encryption_key: str = "CHANGE_THIS_32_BYTE_ENCRYPTION_KEY"

    backend_api_url: str = "http://localhost:8000"
    cors_origins_raw: str = "http://localhost,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @field_validator("cors_origins_raw")
    @classmethod
    def validate_cors_origins_raw(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",")]
        if not origins or any(not origin for origin in origins):
            raise ValueError("cors_origins_raw must contain comma-separated non-empty origins")
        for origin in origins:
            cls._validate_origin(origin)
        return value

    @model_validator(mode="after")
    def validate_production_table_creation(self):
        if self.app_env == "production" and self.create_tables_on_startup:
            warnings.warn(
                "create_tables_on_startup must be False in production; disabling auto table creation.",
                RuntimeWarning,
                stacklevel=2,
            )
            self.create_tables_on_startup = False
        return self

    @staticmethod
    def _validate_origin(origin: str) -> str:
        parsed_url = urlparse(origin)
        if not origin or origin == "*" or not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid CORS origin: {origin}")
        return origin

    @property
    def database_url_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_with_pool(self) -> str:
        return (
            f"{self.database_url}?"
            f"pool_size={self.db_pool_size}&"
            f"max_overflow={self.db_max_overflow}&"
            f"pool_timeout={self.db_pool_timeout}&"
            f"pool_recycle={self.db_pool_recycle}&"
            f"pre_ping=true"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins(self) -> list[str]:
        return [
            self._validate_origin(origin.strip())
            for origin in self.cors_origins_raw.split(",")
        ]

    @property
    def cors_origins_list(self) -> list[str]:
        return self.cors_origins

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
