from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "APEX"
    app_env: str = "development"
    debug: bool = True
    create_tables_on_startup: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    postgres_user: str = "apex"
    postgres_password: str = "apex_password"
    postgres_db: str = "apex_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

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

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
