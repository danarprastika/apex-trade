"""Service registry implementation."""

from __future__ import annotations

from inspect import isawaitable
from typing import TypeVar, cast

from app.core.exceptions import ServiceRegistrationError, ServiceResolutionError
from app.shared.enums import DependencyScope
from app.shared.protocols import Disposable

from .provider import FactoryContext, ProviderFunction

T = TypeVar("T")


class Registry:
    """Registry for dependency providers."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._providers: dict[str, ProviderFunction[object]] = {}
        self._scopes: dict[str, DependencyScope] = {}
        self._singletons: dict[str, object] = {}

    def register(
        self,
        name: str,
        provider: ProviderFunction[T],
        *,
        scope: DependencyScope = DependencyScope.TRANSIENT,
    ) -> None:
        """Register a dependency provider."""
        if not name.strip():
            raise ServiceRegistrationError("Service name must not be empty", "EMPTY_SERVICE_NAME")
        self._providers[name] = cast(ProviderFunction[object], provider)
        self._scopes[name] = scope
        if scope is DependencyScope.SINGLETON:
            self._singletons.pop(name, None)

    def unregister(self, name: str) -> None:
        """Unregister a dependency by name."""
        self._providers.pop(name, None)
        self._scopes.pop(name, None)
        self._singletons.pop(name, None)

    def has(self, name: str) -> bool:
        """Return whether a dependency is registered."""
        return name in self._providers

    def names(self) -> tuple[str, ...]:
        """Return registered dependency names."""
        return tuple(sorted(self._providers))

    def provider_for(self, name: str) -> ProviderFunction[object]:
        """Return a provider by name."""
        provider = self._providers.get(name)
        if provider is None:
            raise ServiceResolutionError(f"Dependency not found: {name}", "DEPENDENCY_NOT_FOUND")
        return provider

    def scope_for(self, name: str) -> DependencyScope:
        """Return the scope for a registered dependency."""
        scope = self._scopes.get(name)
        if scope is None:
            raise ServiceResolutionError(
                f"Unknown dependency scope: {name}", "UNKNOWN_DEPENDENCY_SCOPE"
            )
        return scope

    async def resolve(self, name: str, *, container: object | None = None) -> object:
        """Resolve a dependency by name."""
        provider = self.provider_for(name)

        scope = self._scopes[name]
        if scope is DependencyScope.SINGLETON and name in self._singletons:
            return self._singletons[name]

        context = FactoryContext(name=name, scope=scope, container=container or self)
        value = provider(context)
        if isawaitable(value):
            value = await value

        if scope is DependencyScope.SINGLETON:
            self._singletons[name] = value
        return value

    async def close(self) -> None:
        """Close disposable singleton instances."""
        for name, value in list(self._singletons.items()):
            if isinstance(value, Disposable):
                close_result = value.close()
                if isawaitable(close_result):
                    await close_result
            self._singletons.pop(name, None)


__all__ = ["Registry"]
