from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_risk_service
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.risk import RiskDecision, RiskEventCreate, RiskEventRead, RiskProfileCreate, RiskProfileRead
from app.services.risk_service import RiskService

router = APIRouter()


@router.get("/profile", response_model=RiskProfileRead)
def get_profile(
    current_user: User = Depends(get_current_user),
    risk_service: RiskService = Depends(get_risk_service),
):
    return risk_service.get_profile(current_user.id)


@router.post("/profile", response_model=RiskProfileRead, status_code=201)
def create_profile(
    payload: RiskProfileCreate,
    current_user: User = Depends(get_current_user),
    risk_service: RiskService = Depends(get_risk_service),
):
    user_id = payload.user_id or current_user.id
    if user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return risk_service.create_profile(
        user_id=user_id,
        max_risk_per_trade=payload.max_risk_per_trade,
        max_daily_loss=payload.max_daily_loss,
        max_drawdown=payload.max_drawdown,
        max_open_positions=payload.max_open_positions,
    )


@router.get("/events", response_model=list[RiskEventRead])
def list_events(
    current_user: User = Depends(get_current_user),
    risk_service: RiskService = Depends(get_risk_service),
):
    return risk_service.list_events(current_user.id)


@router.post("/events", response_model=RiskEventRead, status_code=201)
def create_event(
    payload: RiskEventCreate,
    current_user: User = Depends(get_current_user),
    risk_service: RiskService = Depends(get_risk_service),
):
    return risk_service.log_event(
        user_id=payload.user_id or current_user.id,
        event_type=payload.event_type,
        severity=payload.severity,
        description=payload.description,
    )


@router.post("/validate", response_model=RiskDecision)
def validate_risk(
    risk_score: float,
    requested_position_size: float | None = None,
    current_user: User = Depends(get_current_user),
    risk_service: RiskService = Depends(get_risk_service),
):
    return risk_service.evaluate(current_user.id, risk_score, requested_position_size)



