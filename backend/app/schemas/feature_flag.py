from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    USER = "user"
    ROLE = "role"
    SEGMENT = "segment"


class FeatureFlagCreate(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    enabled: bool = False
    environment: str = Field(default="development", min_length=1, max_length=20)
    owner: str | None = Field(default=None, max_length=100)
    metadata: dict[str, Any] | None = None
    is_kill_switch: bool = False
    failure_mode: str = Field(default="fail_closed", min_length=1, max_length=20)
    reason: str | None = Field(default=None, max_length=500)


class FeatureFlagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None
    environment: str | None = Field(default=None, min_length=1, max_length=20)
    owner: str | None = Field(default=None, max_length=100)
    metadata: dict[str, Any] | None = None
    is_kill_switch: bool | None = None
    failure_mode: str | None = Field(default=None, min_length=1, max_length=20)
    reason: str | None = Field(default=None, max_length=500)


class AssignmentCreate(BaseModel):
    target_type: TargetType
    target_id: str | None = Field(default=None, max_length=100)
    target_role: str | None = Field(default=None, max_length=20)
    rollout_percentage: float | None = Field(default=None, ge=0, le=100)
    environment: str | None = Field(default=None, max_length=20)
    enabled: bool = True
    metadata: dict[str, Any] | None = None


class AssignmentRead(BaseModel):
    id: str
    target_type: str
    target_id: str | None
    target_role: str | None
    rollout_percentage: float | None
    environment: str | None
    enabled: bool
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class FeatureFlagRead(BaseModel):
    id: str
    key: str
    name: str
    description: str | None
    enabled: bool
    environment: str
    owner: str | None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    is_kill_switch: bool
    failure_mode: str
    created_at: str
    updated_at: str
    assignments: list[AssignmentRead] = []

    model_config = {"from_attributes": True}


class FeatureFlagAuditLogRead(BaseModel):
    id: int
    flag_key: str
    action: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    actor_user_id: str | None
    actor_role: str | None
    ip_address: str | None
    reason: str | None
    created_at: str

    model_config = {"from_attributes": True}


class FeatureFlagEvaluateResponse(BaseModel):
    flag_key: str
    enabled: bool
    reason: str
    environment: str
    variant: dict[str, Any] | None
    rollout_bucket: int | None
    user_context: dict[str, Any] | None
    dependencies_evaluated: list[str]
    evaluated_at: str


class FeatureFlagEvaluateRequest(BaseModel):
    flags: list[str] = Field(default_factory=list)


class FeatureFlagEvaluateManyResponse(BaseModel):
    flags: list[FeatureFlagEvaluateResponse]
    environment: str
    user_id: str


class FeatureFlagBootstrapResponse(BaseModel):
    flags: list[FeatureFlagEvaluateResponse]
    environment: str
    user_id: str
