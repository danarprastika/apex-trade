"""Dependency container facade."""

from __future__ import annotations

from inspect import isawaitable
from typing import TypeVar, cast

from .provider import FactoryContext, ProviderFunction
from .registry import Registry
from .scope import DependencyScope

T = TypeVar("T")


class Container:
    """Facade over the service registry."""

    def __init__(self, registry: Registry | None = None) -> None:
        """Initialize the container."""
        self._registry = registry or Registry()

    @property
    def registry(self) -> Registry:
        """Return the underlying registry."""
        return self._registry

    def register(
        self,
        name: str,
        provider: ProviderFunction[object],
        *,
        scope: DependencyScope = DependencyScope.TRANSIENT,
    ) -> None:
        """Register a dependency provider."""
        self._registry.register(name, provider, scope=scope)

    def has(self, name: str) -> bool:
        """Return whether a dependency is registered."""
        return self._registry.has(name)

    def names(self) -> tuple[str, ...]:
        """Return registered dependency names."""
        return self._registry.names()

    async def resolve(self, name: str) -> T:
        """Resolve a dependency by name."""
        value = await self._registry.resolve(name, container=self)
        return cast(T, value)

    async def resolve_optional(self, name: str) -> T | None:
        """Resolve an optional dependency by name."""
        if not self.has(name):
            return None
        return await self.resolve(name)

    async def close(self) -> None:
        """Close disposable singleton dependencies."""
        await self._registry.close()

    async def call_provider(self, name: str) -> object:
        """Call a provider directly through a factory context."""
        provider = self._registry.provider_for(name)
        context = FactoryContext(name=name, scope=self._registry.scope_for(name), container=self)
        value = provider(context)
        if isawaitable(value):
            return await value
        return value


__all__ = ["Container"]
