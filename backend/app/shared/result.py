"""Result pattern implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Successful result value."""

    value: T


@dataclass(frozen=True, slots=True)
class Err[E]:
    """Failed result value."""

    error: E


type Result[T, E] = Ok[T] | Err[E]

__all__ = ["Err", "Ok", "Result"]
