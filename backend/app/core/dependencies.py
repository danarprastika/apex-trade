"""Dependency registry for the QuantX AI core package.

The registry implements a small dependency-inversion container for core
services. It supports explicit singleton registration, transient factory
registration, provider registration, and circular-dependency detection without
depending on any external DI framework.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Protocol, TypeVar, cast

from .exceptions import (
    CircularDependencyError,
    DependencyAlreadyRegisteredError,
    DependencyInjectionError,
    DependencyNotFoundError,
)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class DependencyProvider(Protocol[T_co]):
    """Protocol for objects that provide dependencies."""

    def provide(self, registry: DependencyRegistry) -> T_co:
        """Provide a dependency instance."""
        ...


class DependencyRegistry:
    """Resolve dependencies registered by interface type."""

    def __init__(self) -> None:
        """Create an empty dependency registry."""
        self._singletons: dict[type[object], object] = {}
        self._factories: dict[type[object], Callable[..., object]] = {}
        self._resolving: set[type[object]] = set()

    def register_singleton(self, interface: type[T], instance: T) -> DependencyRegistry:
        """Register an existing instance as a singleton dependency."""
        key = self._key(interface)
        self._ensure_not_registered(key, interface.__name__)
        self._singletons[key] = cast(object, instance)
        return self

    def register_factory(self, interface: type[T], factory: Callable[..., T]) -> DependencyRegistry:
        """Register a factory that creates a dependency instance."""
        key = self._key(interface)
        self._ensure_not_registered(key, interface.__name__)
        self._factories[key] = cast(Callable[..., object], factory)
        return self

    def register_provider(self, interface: type[T], provider: DependencyProvider[T]) -> DependencyRegistry:
        """Register a provider object that creates a dependency instance."""

        def factory(registry: DependencyRegistry) -> T:
            """Create a dependency from a provider."""
            return provider.provide(registry)

        return self.register_factory(interface, factory)

    def has(self, interface: type[object]) -> bool:
        """Return whether a dependency is registered."""
        key = self._key(interface)
        return key in self._singletons or key in self._factories

    def get(self, interface: type[T]) -> T:
        """Resolve and return a dependency instance."""
        key = self._key(interface)
        if key in self._singletons:
            return cast(T, self._singletons[key])

        factory = self._factories.get(key)
        if factory is None:
            raise DependencyNotFoundError(interface.__name__)
        if key in self._resolving:
            raise CircularDependencyError(interface.__name__)

        self._resolving.add(key)
        try:
            return cast(T, self._call_factory(factory))
        except DependencyInjectionError:
            raise
        except Exception as exc:
            raise DependencyInjectionError(
                message=f"Failed to resolve dependency '{interface.__name__}'",
                details={"dependency": interface.__name__},
            ) from exc
        finally:
            self._resolving.discard(key)

    def clear(self) -> DependencyRegistry:
        """Remove all registered dependencies."""
        self._singletons.clear()
        self._factories.clear()
        self._resolving.clear()
        return self

    def _ensure_not_registered(self, key: type[object], dependency_name: str) -> None:
        """Ensure a dependency is not already registered."""
        if key in self._singletons or key in self._factories:
            raise DependencyAlreadyRegisteredError(dependency_name)

    def _call_factory(self, factory: Callable[..., object]) -> object:
        """Call a factory with zero parameters or this registry."""
        try:
            signature = inspect.signature(factory)
        except (TypeError, ValueError) as exc:
            raise DependencyInjectionError("Dependency factory signature is invalid") from exc

        parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            }
        ]

        if len(parameters) == 0:
            return factory()
        if len(parameters) == 1:
            return factory(self)

        raise DependencyInjectionError(
            message="Dependency factory must accept zero parameters or the registry",
            details={"parameters": len(parameters)},
        )

    @staticmethod
    def _key(interface: type[object]) -> type[object]:
        """Return the registry key for an interface."""
        return interface


__all__ = ["DependencyProvider", "DependencyRegistry"]
