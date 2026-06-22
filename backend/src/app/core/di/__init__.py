"""Dependency injection package."""

from __future__ import annotations

from .container import Container
from .provider import FactoryContext, ProviderFunction
from .registry import Registry
from .scope import DependencyScope

__all__ = ["Container", "DependencyScope", "FactoryContext", "ProviderFunction", "Registry"]
