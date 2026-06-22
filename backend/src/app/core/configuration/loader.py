"""Settings loader for Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from .settings import ApplicationSettings


class SettingsLoader:
    """Load application settings from environment sources."""

    @staticmethod
    def load(env_file: str | Path | None = None) -> ApplicationSettings:
        """Load and return application settings."""
        if env_file is None:
            return ApplicationSettings()
        return ApplicationSettings(_env_file=Path(env_file))  # type: ignore[call-arg]


__all__ = ["SettingsLoader"]
