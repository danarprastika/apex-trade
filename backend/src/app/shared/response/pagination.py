"""Pagination metadata for API responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=500)
    total_items: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)


__all__ = ["PaginationMeta"]
