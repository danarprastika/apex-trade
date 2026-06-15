from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_market_service
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.market import AssetCreate, AssetRead, CandleCreate, CandleRead, MarketPairCreate, MarketPairRead
from app.services.market_service import MarketService

router = APIRouter()


@router.get("/assets", response_model=list[AssetRead])
def list_assets(
    market_service: MarketService = Depends(get_market_service),
):
    return market_service.list_assets()


@router.post("/assets", response_model=AssetRead, status_code=201)
def create_asset(
    payload: AssetCreate,
    current_user: User = Depends(get_current_user),
    market_service: MarketService = Depends(get_market_service),
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return market_service.create_asset(payload.symbol, payload.asset_type, payload.name)


@router.get("/pairs", response_model=list[MarketPairRead])
def list_pairs(
    market_service: MarketService = Depends(get_market_service),
):
    return market_service.list_market_pairs()


@router.post("/pairs", response_model=MarketPairRead, status_code=201)
def create_pair(
    payload: MarketPairCreate,
    current_user: User = Depends(get_current_user),
    market_service: MarketService = Depends(get_market_service),
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return market_service.create_market_pair(
        payload.exchange_id,
        payload.base_asset_id,
        payload.quote_asset_id,
        payload.symbol,
    )


@router.get("/candles", response_model=list[CandleRead])
def list_candles(
    market_pair_id: str,
    timeframe: str = "1h",
    limit: int = Query(100, ge=1, le=1000),
    market_service: MarketService = Depends(get_market_service),
):
    return market_service.list_candles(market_pair_id, timeframe, limit=limit)


@router.post("/candles", response_model=CandleRead, status_code=201)
def create_candle(
    payload: CandleCreate,
    current_user: User = Depends(get_current_user),
    market_service: MarketService = Depends(get_market_service),
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return market_service.create_candle(
        payload.market_pair_id,
        payload.timeframe,
        payload.open,
        payload.high,
        payload.low,
        payload.close,
        payload.volume,
        payload.open_time,
        payload.close_time,
    )



