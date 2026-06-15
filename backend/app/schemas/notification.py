from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    user_id: str | None = None
    notification_type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=2000)


class NotificationRead(BaseModel):
    id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    status: str
    sent_at: datetime | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
