"""Lifecycle hook protocol."""

from __future__ import annotations

from typing import Protocol


class LifecycleHook(Protocol):
    """Protocol for lifecycle hooks."""

    name: str

    async def __call__(self, context: object) -> None:
        """Execute the lifecycle hook."""
        ...


__all__ = ["LifecycleHook"]
