"""FastAPI dependencies."""

from src.infrastructure.config.settings import Settings
from src.infrastructure.config.settings import settings as _settings


def get_settings() -> Settings:
    """Get application settings."""
    return _settings
