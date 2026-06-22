"""Provider function types."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .scope import DependencyScope


@dataclass(frozen=True, slots=True)
class FactoryContext:
    """Context passed to dependency providers."""

    name: str
    scope: DependencyScope
    container: object

    def metadata(self) -> dict[str, object]:
        """Return context metadata."""
        return {
            "name": self.name,
            "scope": self.scope.value,
        }


type ProviderFunction[T] = Callable[[FactoryContext], T | Awaitable[T]]

__all__ = ["DependencyScope", "FactoryContext", "ProviderFunction"]
