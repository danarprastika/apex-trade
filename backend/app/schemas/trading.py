from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StrategyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=50)
    version: str = Field(min_length=1, max_length=20)
    strategy_type: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)


class StrategyRead(BaseModel):
    id: str
    name: str
    code: str
    version: str
    description: str | None
    strategy_type: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SignalCreate(BaseModel):
    strategy_id: str
    market_pair_id: str
    signal_type: str = Field(min_length=3, max_length=20)
    confidence: float = Field(ge=0, le=100)
    entry_price: float = Field(gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("take_profit", "stop_loss")
    @classmethod
    def validate_stop_take(cls, value: float | None, info) -> float | None:
        if value is not None and info.data.get("entry_price") is not None:
            if info.data.get("stop_loss") is not None and info.data.get("take_profit") is not None:
                if info.data["take_profit"] <= info.data["entry_price"] <= info.data["stop_loss"]:
                    raise ValueError("take_profit must be above entry_price and stop_loss below entry_price")
        return value


class SignalRead(BaseModel):
    id: str
    strategy_id: str
    market_pair_id: str
    signal_type: str
    confidence: float
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    reason: str
    signal_time: datetime
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    exchange_account_id: str
    signal_id: str | None = None
    order_type: str = Field(min_length=3, max_length=20)
    side: str = Field(min_length=3, max_length=20)
    quantity: float = Field(gt=0)
    price: float | None = Field(default=None, gt=0)
    risk_score: float | None = Field(default=None, ge=0, le=100)


class PaperOrderCreate(BaseModel):
    market_pair_id: str
    strategy_id: str
    signal_id: str | None = None
    side: str = Field(min_length=3, max_length=20)
    quantity: float = Field(gt=0)
    price: float | None = Field(default=None, gt=0)


class PaperOrderRead(BaseModel):
    order: OrderRead
    position: PositionRead | None = None
    trade: TradeRead | None = None
    risk_allowed: bool
    risk_reason: str
    message: str


class OrderRead(BaseModel):
    id: str
    exchange_account_id: str
    signal_id: str | None
    exchange_order_id: str | None
    order_type: str
    side: str
    quantity: float
    price: float | None
    filled_quantity: float
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PositionRead(BaseModel):
    id: str
    exchange_account_id: str
    market_pair_id: str
    strategy_id: str
    entry_order_id: str | None
    entry_price: float
    quantity: float
    current_price: float
    unrealized_pnl: float
    status: str
    opened_at: datetime
    closed_at: datetime | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TradeRead(BaseModel):
    id: str
    position_id: str
    strategy_id: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_profit: float
    net_profit: float
    profit_percentage: float
    duration_minutes: int
    opened_at: datetime
    closed_at: datetime
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
