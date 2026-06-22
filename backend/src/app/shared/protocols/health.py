"""Health check protocol."""

from __future__ import annotations

from typing import Protocol


class HealthCheck(Protocol):
    """Protocol for health checks."""

    name: str

    async def check(self) -> object:
        """Run the health check and return its raw result."""
        ...


__all__ = ["HealthCheck"]
