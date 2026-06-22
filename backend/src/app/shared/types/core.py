"""Core shared type aliases."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime

type Timestamp = datetime
type UUIDString = str
type MaybeAsync = Callable[[], object | Awaitable[object]]
type AsyncMaybe = Awaitable[object]

__all__ = ["AsyncMaybe", "MaybeAsync", "Timestamp", "UUIDString"]
