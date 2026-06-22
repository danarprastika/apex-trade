"""Structured JSON logging formatter."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.configuration import LoggingSettings
from app.core.logging.sanitizer import sanitize_for_logging


class JsonFormatter(logging.Formatter):
    """Logging formatter that emits one JSON object per record."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(sanitize_for_logging(payload), ensure_ascii=False)


def create_json_formatter(format_string: str) -> JsonFormatter:
    """Create a JSON log formatter."""
    return JsonFormatter(fmt=format_string)


def configure_logging(settings: LoggingSettings, *, force: bool = False) -> None:
    """Configure root logging with structured JSON output."""
    root_logger = logging.getLogger()
    if force:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    if not root_logger.handlers:
        handler = _create_handler(settings)
        handler.setFormatter(create_json_formatter(settings.format))
        root_logger.addHandler(handler)

    root_logger.setLevel(getattr(logging, settings.level.upper(), logging.INFO))


def _create_handler(settings: LoggingSettings) -> logging.Handler:
    """Create the configured log handler."""
    if settings.file_path is None:
        return logging.StreamHandler()

    path = Path(settings.file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return RotatingFileHandler(path, maxBytes=10_000_000, backupCount=5, encoding="utf-8")


__all__ = ["JsonFormatter", "configure_logging", "create_json_formatter"]
