from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.domain.safety.value_objects import KillSwitchScope, SafetyContext, ValidationLayer
from app.schemas.trading_safety import (
    ExposureLimitCreate,
    ExposureLimitRead,
    KillSwitchAuditLogRead,
    KillSwitchStateRead,
    KillSwitchTrigger,
    SafetyDecision,
    SafetyHealth,
)
from app.services.trading_safety.kill_switch_service import KillSwitchService
from app.services.trading_safety.exposure_monitor import ExposureMonitor

router = APIRouter()


@router.get("/killswitch", response_model=list[KillSwitchStateRead])
async def list_kill_switches(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    scope: str | None = None,
):
    async with db:
        kill_service = KillSwitchService(db)
        if scope:
            return await kill_service.kill_states.list_by_scope(scope)
        return []


@router.get("/killswitch/{scope}/{scope_id}", response_model=KillSwitchStateRead)
async def get_kill_switch(
    scope: str,
    scope_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    async with db:
        kill_service = KillSwitchService(db)
        state = await kill_service.kill_states.get_active(scope, scope_id)
        if not state:
            raise HTTPException(status_code=404, detail="Kill switch state not found")
        return state


@router.post("/killswitch/{scope}", status_code=status.HTTP_204_NO_CONTENT)
async def trigger_kill_switch(
    scope: str,
    payload: KillSwitchTrigger,
    scope_id: str | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if scope == KillSwitchScope.GLOBAL.value and current_user.role != ROLE_SUPER_ADMIN:
        raise PermissionDeniedError("Only SUPER_ADMIN can trigger global kill switch")
    async with db:
        kill_service = KillSwitchService(db)
        await kill_service.trigger_kill(
            scope=KillSwitchScope(scope.upper()),
            scope_id=scope_id,
            triggered_by=current_user.id,
            actor_role=current_user.role,
            ip_address=None,
            reason=payload.reason,
            expires_at=payload.expires_at,
        )


@router.delete("/killswitch/{scope}/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_kill_switch(
    scope: str,
    scope_id: str,
    reason: str | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    async with db:
        kill_service = KillSwitchService(db)
        await kill_service.clear_kill(
            scope=KillSwitchScope(scope.upper()),
            scope_id=scope_id,
            cleared_by=current_user.id,
            actor_role=current_user.role,
            ip_address=None,
            reason=reason or "manual_clear",
        )


@router.post("/validate/pre-trade", response_model=SafetyDecision)
async def validate_pre_trade(
    exchange_account_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    symbol: str | None = None,
    side: str | None = None,
    order_type: str | None = None,
    quantity: float | None = None,
    price: float | None = None,
    strategy_id: str | None = None,
):
    from app.services.trading_safety import SafetyOrchestrator

    context = SafetyContext(
        user_id=current_user.id,
        exchange_account_id=exchange_account_id,
        strategy_id=strategy_id,
        symbol=symbol or "",
        side=side or "",
        order_type=order_type or "",
        quantity=quantity,
        price=price,
    )
    async with db:
        orchestrator = SafetyOrchestrator(db)
        return await orchestrator.validate_pre_trade(context)


@router.get("/exposure/{user_id}", response_model=list[ExposureLimitRead])
async def get_user_exposures(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    async with db:
        monitor = ExposureMonitor(db)
        return await monitor.exposure_limits.get_all_for_user(user_id)


@router.post("/exposure", response_model=ExposureLimitRead, status_code=status.HTTP_201_CREATED)
async def set_exposure_limit(
    payload: ExposureLimitCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = payload.user_id or current_user.id
    if user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    async with db:
        monitor = ExposureMonitor(db)
        return await monitor.set_limit(
            user_id=user_id,
            scope=payload.scope,
            max_exposure_percentage=payload.max_exposure_percentage,
            exchange_id=payload.exchange_id,
            asset_id=payload.asset_id,
        )


@router.post("/validate/post-trade", response_model=SafetyDecision)
async def validate_post_trade(
    order_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    exchange_account_id: str | None = None,
):
    from app.services.trading_safety import SafetyOrchestrator

    class MockContext:
        user_id: str = current_user.id
        exchange_id: str | None = None

    async with db:
        orchestrator = SafetyOrchestrator(db)
        try:
            decision = await orchestrator.validate_post_trade(order_id, None, MockContext())
            if decision.approved:
                decision.add_success(ValidationLayer.KILL_SWITCH)
            return decision
        except PermissionDeniedError:
            raise
        except Exception as e:
            decision = SafetyDecision(approved=False, reasons=[f"Validation error: {e}"], checks_performed={}, execution_blocked_by=["error"])
            return decision


@router.get("/health/safety", response_model=SafetyHealth)
async def get_safety_health(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    async with db:
        from app.services.trading_safety import SafetyOrchestrator

        orchestrator = SafetyOrchestrator(db)
        health = orchestrator.get_health_status()
        return SafetyHealth(**health)
