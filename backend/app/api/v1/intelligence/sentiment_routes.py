from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_TRADER, ROLE_VIEWER
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.intelligence import FearGreedSnapshotRead, SentimentRecordRead

router = APIRouter()


@router.get("/social", response_model=list[SentimentRecordRead])
def list_sentiment(
    asset_id: str | None = None,
    platform: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    return []


@router.get("/assets/{asset_id}", response_model=dict)
def get_asset_sentiment(asset_id: str):
    return {"sentiment_score": 50.0, "confidence": 0.0, "count": 0}


@router.get("/market", response_model=dict)
def get_market_sentiment():
    return {"sentiment_score": 50.0, "confidence": 0.0}


@router.get("/fear-greed", response_model=FearGreedSnapshotRead)
def get_fear_greed(scope_type: str = "MARKET", scope_id: str = "global"):
    return FearGreedSnapshotRead(
        id=1,
        scope_type=scope_type,
        scope_id=scope_id,
        index_value=50.0,
        index_label="Neutral",
        captured_at=None,
    )


@router.get("/fear-greed/history", response_model=list[FearGreedSnapshotRead])
def get_fear_greed_history(scope_type: str = "MARKET", scope_id: str = "global", limit: int = 100):
    return []


@router.post("/refresh")
def refresh_sentiment(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    from app.tasks.collectors.intelligence_collector import fetch_sentiment
    fetch_sentiment.delay()
    return {"status": "refresh triggered"}