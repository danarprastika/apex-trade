from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.intelligence import NewsArticleRead, NewsEventRead

router = APIRouter()


@router.get("", response_model=list[NewsArticleRead])
def list_news(
    asset_id: str | None = None,
    market_pair_id: str | None = None,
    category: str | None = None,
    min_impact_score: float | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    return []


@router.get("/events", response_model=list[NewsEventRead])
def list_news_events(
    event_type: str | None = None,
    asset_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    return []