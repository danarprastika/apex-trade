"""Correlation ID support for request tracing."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from uuid import uuid4

_CORRELATION_ID: ContextVar[str | None] = ContextVar("quantx_correlation_id", default=None)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid4())


def get_correlation_id() -> str | None:
    """Return the current correlation ID."""
    return _CORRELATION_ID.get()


def set_correlation_id(correlation_id: str | None) -> Token[str | None]:
    """Set the current correlation ID and return the context token."""
    return _CORRELATION_ID.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the current correlation ID."""
    _CORRELATION_ID.set(None)


@asynccontextmanager
async def correlation_id_context(correlation_id: str | None = None) -> AsyncIterator[str]:
    """Run code with a correlation ID context."""
    resolved = correlation_id or generate_correlation_id()
    previous = set_correlation_id(resolved)
    try:
        yield resolved
    finally:
        _CORRELATION_ID.reset(previous)


__all__ = [
    "clear_correlation_id",
    "correlation_id_context",
    "generate_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
]
