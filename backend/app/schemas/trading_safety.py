from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KillSwitchScope(str):
    GLOBAL = "GLOBAL"
    USER = "USER"
    EXCHANGE = "EXCHANGE"
    STRATEGY = "STRATEGY"


class KillSwitchStateRead(BaseModel):
    id: str
    scope: str
    scope_id: str | None = None
    enabled: bool
    reason: str | None = None
    triggered_by: str | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KillSwitchTrigger(BaseModel):
    enabled: bool = True
    reason: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None


class KillSwitchAuditLogRead(BaseModel):
    id: int
    scope: str
    scope_id: str | None = None
    action: str
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    actor_user_id: str | None = None
    actor_role: str | None = None
    ip_address: str | None = None
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SafetyContext(BaseModel):
    user_id: str
    exchange_account_id: str
    strategy_id: str | None = None
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None


class SafetyDecision(BaseModel):
    approved: bool
    reasons: list[str] = []
    checks_performed: dict[str, bool] = {}
    required_checks: list[str] = []
    execution_blocked_by: list[str] = []
    risk_score: float | None = None
    position_size: float | None = None


class OrderReconciliationLogRead(BaseModel):
    id: str
    order_id: str
    exchange_order_id: str | None = None
    exchange_id: str
    user_id: str
    expected_status: str | None = None
    actual_status: str | None = None
    discrepancy_detected: bool
    resolution_action: str | None = None
    resolution_details: dict[str, Any] | None = None
    resolved_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PositionReconciliationLogRead(BaseModel):
    id: str
    position_id: str
    exchange_position_id: str | None = None
    exchange_id: str
    user_id: str
    expected_quantity: float | None = None
    actual_quantity: float | None = None
    quantity_discrepancy: float | None = None
    expected_entry_price: float | None = None
    actual_entry_price: float | None = None
    price_discrepancy: float | None = None
    discrepancy_detected: bool
    resolution_action: str | None = None
    resolution_details: dict[str, Any] | None = None
    resolved_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketDataQualityEventRead(BaseModel):
    id: str
    market_pair_id: str
    exchange_id: str
    data_type: str
    quality_score: float | None = None
    issues: dict[str, Any] | None = None
    is_valid: bool
    resolved_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExposureLimitRead(BaseModel):
    id: str
    user_id: str
    exchange_id: str | None = None
    asset_id: str | None = None
    max_exposure_percentage: float
    current_exposure_percentage: float
    scope: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExposureLimitCreate(BaseModel):
    user_id: str | None = None
    exchange_id: str | None = None
    asset_id: str | None = None
    scope: str
    max_exposure_percentage: float = Field(gt=0, le=100)


class SafetyHealthComponent(BaseModel):
    status: str


class SafetyHealth(BaseModel):
    status: str
    components: dict[str, SafetyHealthComponent]