"""Collection helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def deep_merge(base: dict[str, object], override: Mapping[str, object]) -> dict[str, object]:
    """Recursively merge two dictionaries."""
    merged = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, Mapping):
            merged[key] = deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def unique_preserve_order[T](values: Sequence[T]) -> tuple[T, ...]:
    """Return unique values while preserving order."""
    seen: set[T] = set()
    unique: list[T] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return tuple(unique)


__all__ = ["deep_merge", "unique_preserve_order"]
