"""Disposable resource protocol."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol, runtime_checkable


@runtime_checkable
class Disposable(Protocol):
    """Protocol for resources that can be closed."""

    def close(self) -> None | Awaitable[None]:
        """Close the resource."""
        ...


__all__ = ["Disposable"]
