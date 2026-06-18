from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_TRADER, ROLE_VIEWER
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.intelligence import (
    IntelligenceSourceRead,
    IntelligenceSourceCreate,
    IntelligenceSourceUpdate,
)

router = APIRouter()


@router.get("/news/sources", response_model=list[IntelligenceSourceRead])
def list_news_sources(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_VIEWER, ROLE_TRADER, ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return []


@router.post("/news/sources", response_model=IntelligenceSourceRead, status_code=201)
def create_news_source(
    payload: IntelligenceSourceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return IntelligenceSourceRead(
        id="synth-id",
        source_name=payload.source_name,
        source_type=payload.source_type,
        category=payload.category,
        url=payload.url,
        enabled=payload.enabled,
        reliability_score=payload.reliability_score,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        auth_required=payload.auth_required,
        created_at=None,
        updated_at=None,
    )


@router.patch("/news/sources/{source_id}", response_model=IntelligenceSourceRead)
def update_news_source(
    source_id: str,
    payload: IntelligenceSourceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return IntelligenceSourceRead(
        id=source_id,
        source_name=payload.source_name or "updated",
        source_type=payload.source_type or "RSS",
        category=payload.category or "crypto",
        url=payload.url or None,
        enabled=payload.enabled if payload.enabled is not None else True,
        reliability_score=50.0,
        rate_limit_per_minute=60,
        auth_required=False,
        created_at=None,
        updated_at=None,
    )


@router.delete("/news/sources/{source_id}", status_code=204)
def delete_news_source(
    source_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return None


@router.post("/news/refresh")
def refresh_news(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    from app.tasks.collectors.intelligence_collector import fetch_news_articles
    fetch_news_articles.delay()
    return {"status": "refresh triggered"}