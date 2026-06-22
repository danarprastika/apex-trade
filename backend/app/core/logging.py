"""Structured logging support for the QuantX AI core package."""

from __future__ import annotations

import logging as std_logging
import uuid
from collections.abc import Generator, Iterable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import cast

from .constants import DEFAULT_CORRELATION_ID_HEADER, DEFAULT_SENSITIVE_FIELD_NAMES
from .settings import CoreSettings, load_settings

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]

_CORRELATION_ID: ContextVar[str | None] = ContextVar("quantx_correlation_id", default=None)


class JsonFormatter(std_logging.Formatter):
    """Format log records as JSON with redacted sensitive fields."""

    def __init__(self, sensitive_fields: Iterable[str] | None = None) -> None:
        """Create a JSON formatter."""
        super().__init__()
        self._sensitive_fields = frozenset(sensitive_fields or DEFAULT_SENSITIVE_FIELD_NAMES)

    def format(self, record: std_logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        payload = self._record_to_dict(record)
        return self._json_dumps(payload)

    def _record_to_dict(self, record: std_logging.LogRecord) -> JsonDict:
        """Convert a log record into a JSON-compatible dictionary."""
        payload: JsonDict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat().replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "level_number": record.levelno,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "process_name": record.processName,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        correlation_id = _CORRELATION_ID.get()
        if correlation_id is not None:
            payload["correlation_id"] = correlation_id

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        context = cast(Mapping[str, object] | None, getattr(record, "quantx_context", None))
        if context:
            for key, value in context.items():
                payload[str(key)] = self._jsonify(value, self._is_sensitive(str(key)))

        for key, value in record.__dict__.items():
            if key in {"args", "asctime", "created", "exc_info", "exc_text", "message", "msg"}:
                continue
            if key.startswith("_") or key in payload:
                continue
            if isinstance(value, Mapping):
                payload[str(key)] = {
                    str(item_key): self._jsonify(item_value, self._is_sensitive(str(item_key)))
                    for item_key, item_value in value.items()
                }
            else:
                payload[str(key)] = self._jsonify(value, self._is_sensitive(str(key)))

        return payload

    def _is_sensitive(self, key: str) -> bool:
        """Return whether a log field name contains sensitive data."""
        normalized = key.lower().replace("-", "_").replace(" ", "_").replace(".", "_")
        return any(field in normalized for field in self._sensitive_fields)

    def _jsonify(self, value: object, sensitive: bool) -> JsonValue:
        """Convert arbitrary values into JSON-compatible values."""
        if sensitive:
            return "[REDACTED]"
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, Mapping):
            return {
                str(key): self._jsonify(item, self._is_sensitive(str(key)))
                for key, item in value.items()
            }
        if isinstance(value, Iterable) and not isinstance(value, str | bytes | bytearray):
            return [self._jsonify(item, False) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, BaseException):
            return str(value)
        return str(value)

    def _json_dumps(self, payload: JsonDict) -> str:
        """Serialize a JSON dictionary without introducing indentation."""
        import json

        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_logger(name: str | None = None) -> std_logging.Logger:
    """Return a logger scoped to the QuantX application."""
    return std_logging.getLogger(name or "app.core")


def generate_correlation_id() -> str:
    """Generate a correlation identifier for a request or background task."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str | None) -> Token[str | None]:
    """Set the correlation identifier for the current context."""
    return _CORRELATION_ID.set(correlation_id)


def get_correlation_id(default: str | None = None) -> str | None:
    """Return the correlation identifier for the current context."""
    return _CORRELATION_ID.get() or default


@contextmanager
def correlation_context(correlation_id: str | None = None) -> Generator[None, None, None]:
    """Run code with an optional correlation identifier."""
    token = set_correlation_id(correlation_id or generate_correlation_id())
    try:
        yield
    finally:
        _CORRELATION_ID.reset(token)


def log_with_context(
    logger: std_logging.Logger,
    level: int,
    message: str,
    context: Mapping[str, object] | None = None,
    *,
    exc_info: bool = False,
) -> None:
    """Log a structured message with contextual fields."""
    logger.log(level, message, extra={"quantx_context": dict(context or {})}, exc_info=exc_info)


def configure_logging(settings: CoreSettings | None = None) -> std_logging.Logger:
    """Configure structured logging for the root logger."""
    resolved_settings = settings or load_settings()
    root_logger = std_logging.getLogger()
    root_logger.setLevel(resolved_settings.log_level.to_stdlib_level())

    if not root_logger.handlers:
        root_logger.addHandler(std_logging.StreamHandler())

    formatter = JsonFormatter(resolved_settings.log_sensitive_field_names)
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    for logger_name in ("app", "app.core"):
        logger = std_logging.getLogger(logger_name)
        logger.setLevel(resolved_settings.log_level.to_stdlib_level())
        logger.propagate = False

    return get_logger()


__all__ = [
    DEFAULT_CORRELATION_ID_HEADER,
    "JsonFormatter",
    "configure_logging",
    "correlation_context",
    "generate_correlation_id",
    "get_correlation_id",
    "get_logger",
    "log_with_context",
    "set_correlation_id",
]
