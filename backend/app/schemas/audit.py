from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogRead(BaseModel):
    id: int
    user_id: str | None
    entity_type: str
    entity_id: str
    action: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogCreate(BaseModel):
    user_id: str | None = None
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: str = Field(min_length=1, max_length=255)
    action: str = Field(min_length=1, max_length=100)
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    ip_address: str | None = None
