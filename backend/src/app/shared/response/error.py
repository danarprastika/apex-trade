"""Standard API error response models."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.exceptions import QuantXBaseError
from app.shared.types import JsonDict


class ErrorDetail(BaseModel):
    """Structured error detail."""

    model_config = ConfigDict(extra="forbid")

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Standard API error response."""

    model_config = ConfigDict(extra="forbid")

    status: str = "error"
    error: JsonDict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_exception(cls, exc: BaseException) -> ErrorResponse:
        """Build an error response from an exception."""
        if isinstance(exc, QuantXBaseError):
            return cls(error=exc.to_dict())
        return cls(
            error={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "retryable": False,
                "severity": "high",
            }
        )


__all__ = ["ErrorDetail", "ErrorResponse"]
