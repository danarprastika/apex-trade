"""Reusable shared primitives for the QuantX AI backend.

This package provides framework-agnostic building blocks including base entities,
result types, response envelopes, protocol definitions, type aliases, utility
functions, and input validators. It contains no business or infrastructure logic.
"""

from __future__ import annotations

from .base import BaseEntity
from .protocols import (
    CacheProtocol,
    LoggerProtocol,
    PublisherProtocol,
    RepositoryProtocol,
    SubscriberProtocol,
)
from .responses import ApiResponse, Meta, PaginatedResponse
from .result import Err, Ok, Result
from .types import AppId, OrderId, SessionId, Symbol, Timestamp, UserId
from .utils import deep_merge, generate_id, generate_nonce, slugify, truncate, utc_now
from .validators import validate_email, validate_url, validate_uuid

__all__ = [
    "AppId",
    "ApiResponse",
    "BaseEntity",
    "CacheProtocol",
    "Err",
    "LoggerProtocol",
    "Meta",
    "Ok",
    "OrderId",
    "PaginatedResponse",
    "PublisherProtocol",
    "RepositoryProtocol",
    "Result",
    "SessionId",
    "SubscriberProtocol",
    "Symbol",
    "Timestamp",
    "UserId",
    "deep_merge",
    "generate_id",
    "generate_nonce",
    "slugify",
    "truncate",
    "utc_now",
    "validate_email",
    "validate_uuid",
    "validate_url",
]
