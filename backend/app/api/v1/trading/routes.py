from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_current_user,
    get_execution_service,
    get_paper_trading_service,
    get_risk_service,
    get_signal_service,
    get_strategy_service,
)
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.trading import (
    OrderCreate,
    OrderRead,
    PaperOrderCreate,
    PaperOrderRead,
    SignalCreate,
    SignalRead,
    StrategyCreate,
    StrategyRead,
)
from app.services.paper_trading_service import PaperTradingService
from app.services.risk_service import RiskService
from app.services.trading_service import ExecutionService, SignalService, StrategyService

router = APIRouter()


@router.get("/strategies", response_model=list[StrategyRead])
async def list_strategies(
    strategy_service: Annotated[StrategyService, Depends(get_strategy_service)],
):
    return await strategy_service.list()


@router.post("/strategies", response_model=StrategyRead, status_code=201)
async def create_strategy(
    payload: StrategyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    strategy_service: Annotated[StrategyService, Depends(get_strategy_service)],
):
    if current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return await strategy_service.create(
        payload.name,
        payload.code,
        payload.version,
        payload.strategy_type,
        payload.description,
    )


@router.get("/signals", response_model=list[SignalRead])
async def list_signals(
    signal_service: Annotated[SignalService, Depends(get_signal_service)],
):
    return await signal_service.list()


@router.post("/signals", response_model=SignalRead, status_code=201)
async def create_signal(
    payload: SignalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    signal_service: Annotated[SignalService, Depends(get_signal_service)],
):
    if current_user.role not in {"TRADER", "ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return await signal_service.create(
        payload.strategy_id,
        payload.market_pair_id,
        payload.signal_type,
        payload.confidence,
        payload.entry_price,
        payload.stop_loss,
        payload.take_profit,
        payload.reason,
    )


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    execution_service: Annotated[ExecutionService, Depends(get_execution_service)],
):
    return await execution_service.list_orders(user_id=current_user.id)


@router.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(
    payload: OrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    execution_service: Annotated[ExecutionService, Depends(get_execution_service)],
    risk_service: Annotated[RiskService, Depends(get_risk_service)],
    signal_service: Annotated[SignalService, Depends(get_signal_service)],
):
    if current_user.role not in {"TRADER", "ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    risk_score = payload.risk_score
    if risk_score is None:
        signal = await signal_service.get(payload.signal_id)
        risk_score = signal.confidence if payload.signal_id else 100.0
    requested_position_size = payload.quantity * (payload.price or 0)
    decision = await risk_service.evaluate(current_user.id, risk_score, requested_position_size)
    if not decision.allowed:
        raise PermissionDeniedError(f"Risk veto: {', '.join(decision.veto_reasons)}")
    return await execution_service.create_order(
        payload.exchange_account_id,
        payload.order_type,
        payload.side,
        payload.quantity,
        signal_id=payload.signal_id,
        price=payload.price,
        user_id=current_user.id,
    )


@router.post("/paper-orders", response_model=PaperOrderRead, status_code=201)
async def create_paper_order(
    payload: PaperOrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    paper_trading_service: Annotated[PaperTradingService, Depends(get_paper_trading_service)],
):
    if current_user.role not in {"TRADER", "ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    result = await paper_trading_service.execute_order(
        user_id=current_user.id,
        market_pair_id=payload.market_pair_id,
        strategy_id=payload.strategy_id,
        side=payload.side,
        quantity=payload.quantity,
        price=payload.price,
        signal_id=payload.signal_id,
    )
    return result.to_dict()
