"""Base exception contract for QuantX AI technical errors."""

from __future__ import annotations

from dataclasses import dataclass

from app.shared.enums import ErrorSeverity
from app.shared.types import JsonDict, JsonValue


@dataclass(frozen=True, slots=True)
class QuantXBaseError(Exception):
    """Base class for QuantX AI technical exceptions.

    The exception carries stable machine-readable metadata while preserving
    Python's normal exception behavior.
    """

    message: str
    code: str
    details: JsonDict | None = None
    retryable: bool = False
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    user_message: str | None = None

    def __post_init__(self) -> None:
        """Validate exception fields after dataclass initialization."""
        if not self.message.strip():
            raise ValueError("message must not be empty")
        if not self.code.strip():
            raise ValueError("code must not be empty")

    def __str__(self) -> str:
        """Return the human-readable error message."""
        return self.message

    def to_dict(self) -> JsonDict:
        """Convert the exception to a JSON-serializable dictionary."""
        data: dict[str, JsonValue] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "severity": self.severity.value,
        }
        if self.details is not None:
            data["details"] = self.details
        if self.user_message is not None:
            data["user_message"] = self.user_message
        return data

    @property
    def context(self) -> dict[str, object]:
        """Return logging-friendly context for the exception."""
        context: dict[str, object] = {
            "error_code": self.code,
            "error_message": self.message,
            "error_severity": self.severity.value,
            "error_retryable": self.retryable,
        }
        if self.details:
            context["error_details"] = self.details
        return context


__all__ = ["QuantXBaseError"]
