"""JSON-compatible recursive type aliases."""

from __future__ import annotations

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]
type JsonList = list[JsonValue]

__all__ = ["JsonDict", "JsonList", "JsonPrimitive", "JsonValue"]
