"""Result pattern implementation."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Never, cast


@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Successful result value."""

    value: T | None = None

    @property
    def is_ok(self) -> bool:
        """Return whether the result is successful."""
        return True

    @property
    def is_err(self) -> bool:
        """Return whether the result is an error."""
        return False


@dataclass(frozen=True, slots=True)
class Err[E]:
    """Failed result value."""

    error: E

    @property
    def is_ok(self) -> bool:
        """Return whether the result is successful."""
        return False

    @property
    def is_err(self) -> bool:
        """Return whether the result is an error."""
        return True


type CoreResult[T, E] = Ok[T] | Err[E]
type AsyncResult[T, E] = Awaitable[CoreResult[T, E]]


def success[T](value: T | None = None) -> CoreResult[T, Never]:
    """Create a successful result."""
    return Ok(value)


def failure[E](error: E) -> CoreResult[Never, E]:
    """Create a failed result."""
    return Err(error)


def is_ok[T, E](result: CoreResult[T, E]) -> bool:
    """Return whether a result is successful."""
    return isinstance(result, Ok)


def is_err[T, E](result: CoreResult[T, E]) -> bool:
    """Return whether a result is failed."""
    return isinstance(result, Err)


def unwrap[T, E](result: CoreResult[T, E]) -> T:
    """Return the success value or raise the wrapped error."""
    if isinstance(result, Ok):
        return cast(T, result.value)
    raise cast(BaseException, result.error)


class Result[T, E]:
    """Typed result factory."""

    @staticmethod
    def ok(value: T | None = None) -> CoreResult[T, Never]:
        """Create a successful result."""
        return success(value)

    @staticmethod
    def err(error: E) -> CoreResult[Never, E]:
        """Create a failed result."""
        return failure(error)

    @staticmethod
    def bind(result: CoreResult[T, E], mapper: Callable[[T], CoreResult[T, E]]) -> CoreResult[T, E]:
        """Map a successful result to another result."""
        if is_err(result):
            return result
        return mapper(cast(T, cast(Ok[T], result).value))


__all__ = [
    "AsyncResult",
    "CoreResult",
    "Err",
    "Ok",
    "Result",
    "failure",
    "is_err",
    "is_ok",
    "success",
    "unwrap",
]
