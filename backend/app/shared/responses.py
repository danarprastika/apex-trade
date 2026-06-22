"""Generic API response models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class Meta:
    """Pagination metadata for API responses."""

    page: int | None = None
    page_size: int | None = None
    total: int | None = None
    has_next: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to a JSON-compatible dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ApiResponse[T]:
    """Standard API response envelope."""

    success: bool
    data: T | None = None
    error: str | None = None
    meta: Meta | None = None

    @classmethod
    def ok(cls, data: T, meta: Meta | None = None) -> ApiResponse[T]:
        """Create a successful API response."""
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def fail(cls, error: str, meta: Meta | None = None) -> ApiResponse[T]:
        """Create a failed API response."""
        return cls(success=False, error=error, meta=meta)

    def to_dict(self) -> dict[str, Any]:
        """Convert the response to a JSON-compatible dictionary."""
        payload: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = self.error
        if self.meta is not None:
            payload["meta"] = self.meta.to_dict()
        return payload


@dataclass
class PaginatedResponse[T]:
    """Paginated API response."""

    items: list[T]
    meta: Meta

    def to_dict(self) -> dict[str, Any]:
        """Convert the paginated response to a JSON-compatible dictionary."""
        return {
            "items": self.items,
            "meta": self.meta.to_dict(),
        }


__all__ = ["ApiResponse", "Meta", "PaginatedResponse"]
