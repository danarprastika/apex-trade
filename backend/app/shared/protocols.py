"""Shared protocol definitions."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    """Protocol for repository implementations."""

    async def get(self, id: str) -> T | None:
        """Retrieve an item by its identifier."""
        ...

    async def list(self) -> list[T]:
        """Retrieve all items."""
        ...

    async def add(self, item: T) -> T:
        """Persist a new item and return it."""
        ...

    async def update(self, id: str, item: T) -> T:
        """Update an existing item and return it."""
        ...

    async def delete(self, id: str) -> bool:
        """Remove an item by its identifier."""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache implementations."""

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value by key."""
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value with an optional time-to-live."""
        ...

    async def delete(self, key: str) -> None:
        """Remove a cached value by key."""
        ...

    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the cache."""
        ...


@runtime_checkable
class PublisherProtocol(Protocol):
    """Protocol for message publishers."""

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Publish a message to a topic."""
        ...


@runtime_checkable
class SubscriberProtocol(Protocol):
    """Protocol for message subscribers."""

    async def subscribe(self, topic: str) -> None:
        """Subscribe to a topic."""
        ...


@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol for structured logging implementations."""

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log a debug-level message."""
        ...

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log an informational message."""
        ...

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log a warning message."""
        ...

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log an error message."""
        ...


__all__ = [
    "CacheProtocol",
    "LoggerProtocol",
    "PublisherProtocol",
    "RepositoryProtocol",
    "SubscriberProtocol",
]
