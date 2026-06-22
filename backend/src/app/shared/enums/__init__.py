"""Shared enumerations package."""

from __future__ import annotations

from .dependency_scope import DependencyScope
from .environment import Environment
from .health import HealthScope, HealthStatus
from .lifecycle import LifecyclePhase
from .result import ResultStatus
from .severity import ErrorSeverity

__all__ = [
    "DependencyScope",
    "Environment",
    "ErrorSeverity",
    "HealthScope",
    "HealthStatus",
    "LifecyclePhase",
    "ResultStatus",
]
