from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_TRADER, ROLE_VIEWER
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.intelligence import IntelligenceAlertRead, IntelligenceSnapshotRead

router = APIRouter()


@router.get("/snapshots", response_model=list[IntelligenceSnapshotRead])
def list_intelligence_snapshots(
    asset_id: str | None = None,
    market_pair_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    return []


@router.get("/current", response_model=list[IntelligenceSnapshotRead])
def get_current_intelligence():
    return []


@router.get("/alerts", response_model=list[IntelligenceAlertRead])
def list_intelligence_alerts(severity: str | None = None, limit: int = 100):
    return []


@router.post("/recalculate")
def recalculate_intelligence(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return {"status": "recalculation triggered"}