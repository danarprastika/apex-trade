"""Generic API response envelope."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiResponse[T](BaseModel):
    """Standard successful API response envelope."""

    model_config = ConfigDict(extra="forbid")

    status: str = "success"
    data: T
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def empty() -> ApiResponse[None]:
        """Create an empty successful response."""
        return ApiResponse[None](data=None)


__all__ = ["ApiResponse"]
