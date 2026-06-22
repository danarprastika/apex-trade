"""Shared protocol package."""

from __future__ import annotations

from .config import ConfigProvider
from .disposable import Disposable
from .health import HealthCheck
from .lifecycle import LifecycleHook

__all__ = ["ConfigProvider", "Disposable", "HealthCheck", "LifecycleHook"]
