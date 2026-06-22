"""Shared type aliases package."""

from __future__ import annotations

from .core import AsyncMaybe, MaybeAsync, Timestamp, UUIDString
from .json import JsonDict, JsonList, JsonPrimitive, JsonValue

__all__ = [
    "AsyncMaybe",
    "JsonDict",
    "JsonList",
    "JsonPrimitive",
    "JsonValue",
    "MaybeAsync",
    "Timestamp",
    "UUIDString",
]
