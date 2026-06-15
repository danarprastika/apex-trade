from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_portfolio_service
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioSnapshotCreate, PortfolioSnapshotRead
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/", response_model=PortfolioRead)
def get_portfolio(
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    return portfolio_service.get_or_create_default(current_user.id)


@router.post("/", response_model=PortfolioRead, status_code=201)
def create_portfolio(
    payload: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    if payload.user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return portfolio_service.create(payload.user_id, payload.portfolio_name, payload.currency)


@router.get("/snapshots", response_model=list[PortfolioSnapshotRead])
def list_snapshots(
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    portfolio = portfolio_service.get_or_create_default(current_user.id)
    return portfolio_service.list_snapshots(portfolio.id)


@router.post("/snapshots", response_model=PortfolioSnapshotRead, status_code=201)
def create_snapshot(
    payload: PortfolioSnapshotCreate,
    current_user: User = Depends(get_current_user),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    portfolio = portfolio_service.get_or_create_default(current_user.id)
    if payload.portfolio_id != portfolio.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return portfolio_service.snapshot(
        payload.portfolio_id,
        payload.total_value,
        payload.cash_balance,
        payload.open_positions,
        payload.daily_pnl,
        payload.total_pnl,
    )



