from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_TRADER, ROLE_VIEWER
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User

router = APIRouter()


@router.get("", response_model=list[dict])
def list_market_regimes(
    market_pair_id: str | None = None,
    timeframe: str = "1h",
    limit: int = Query(100, ge=1, le=1000),
):
    return []


@router.get("/{market_pair_id}", response_model=list[dict])
def get_regime_history(market_pair_id: str, timeframe: str = "1h", limit: int = 100):
    return []


@router.post("/recalculate")
def recalculate_regimes(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return {"status": "recalculation triggered"}