"""Configuration provider protocol."""

from __future__ import annotations

from typing import Protocol


class ConfigProvider(Protocol):
    """Protocol for reading configuration values."""

    def get(self, key: str) -> str | None:
        """Return a configuration value by key."""
        ...


__all__ = ["ConfigProvider"]
