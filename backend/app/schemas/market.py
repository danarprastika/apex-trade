from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AssetCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    name: str | None = Field(default=None, max_length=100)
    asset_type: str = Field(min_length=2, max_length=30)


class AssetRead(BaseModel):
    id: str
    symbol: str
    name: str | None
    asset_type: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MarketPairCreate(BaseModel):
    exchange_id: str
    base_asset_id: str
    quote_asset_id: str
    symbol: str = Field(min_length=1, max_length=50)


class MarketPairRead(BaseModel):
    id: str
    exchange_id: str
    base_asset_id: str
    quote_asset_id: str
    symbol: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CandleCreate(BaseModel):
    market_pair_id: str
    timeframe: str = Field(min_length=1, max_length=10)
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    open_time: datetime
    close_time: datetime

    @field_validator("close_time")
    @classmethod
    def close_after_open(cls, value: datetime, info) -> datetime:
        open_time = info.data.get("open_time")
        if open_time and value <= open_time:
            raise ValueError("close_time must be after open_time")
        return value


class CandleRead(BaseModel):
    id: int
    market_pair_id: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    open_time: datetime
    close_time: datetime

    model_config = {"from_attributes": True}
