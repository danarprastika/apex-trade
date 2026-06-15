from __future__ import annotations

from pydantic import BaseModel, Field


class RiskProfileCreate(BaseModel):
    user_id: str | None = None
    max_risk_per_trade: float = Field(gt=0, le=100)
    max_daily_loss: float = Field(gt=0, le=100)
    max_drawdown: float = Field(gt=0, le=100)
    max_open_positions: int = Field(ge=0)


class RiskProfileRead(BaseModel):
    id: str
    user_id: str
    max_risk_per_trade: float
    max_daily_loss: float
    max_drawdown: float
    max_open_positions: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RiskDecision(BaseModel):
    allowed: bool
    reason: str
    risk_score: float = 0.0
    position_size: float | None = None
    max_risk_per_trade: float = 0.0
    max_daily_loss: float = 0.0
    max_drawdown: float = 0.0
    max_open_positions: int = 0
    open_positions: int = 0
    daily_loss: float = 0.0
    drawdown: float = 0.0
    veto_reasons: list[str] = []


class RiskEventCreate(BaseModel):
    user_id: str | None = None
    event_type: str = Field(min_length=1, max_length=50)
    severity: str = Field(min_length=1, max_length=20)
    description: str = Field(min_length=1, max_length=2000)


class RiskEventRead(BaseModel):
    id: str
    user_id: str
    event_type: str
    severity: str
    description: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
