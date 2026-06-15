from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr


class ExchangeRead(BaseModel):
    id: str
    name: str
    exchange_type: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ExchangeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    exchange_type: str = Field(min_length=2, max_length=80)
    status: str = "ACTIVE"


class ExchangeAccountRead(BaseModel):
    id: str
    user_id: str
    exchange_id: str
    is_testnet: bool
    status: str
    sync_status: str
    last_synced_at: str | None
    balance_snapshot: dict | None = None
    position_snapshot: dict | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ExchangeAccountCreate(BaseModel):
    exchange_id: str
    api_key: SecretStr = Field(min_length=1)
    api_secret: SecretStr = Field(min_length=1)
    is_testnet: bool = False
