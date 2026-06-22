"""Health framework package."""

from __future__ import annotations

from .aggregator import HealthAggregator
from .checks import HealthCheckResult, StaticHealthCheck
from .report import HealthReport

__all__ = ["HealthAggregator", "HealthCheckResult", "HealthReport", "StaticHealthCheck"]
