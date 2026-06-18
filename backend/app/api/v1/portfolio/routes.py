from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_current_user,
    get_db,
    get_portfolio_service,
    get_redis_client_optional,
)
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.portfolio import (
    PerformanceMetricsRead,
    PortfolioAnalyticsRequest,
    PortfolioAnalyticsResponse,
    PortfolioRead,
    PortfolioSnapshotRead,
)
from app.services.portfolio_analytics_service import PortfolioAnalyticsService
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/", response_model=PortfolioRead)
async def get_portfolio(
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
):
    return await portfolio_service.get_or_create_default(current_user.id)


@router.post("/", response_model=PortfolioRead, status_code=201)
async def create_portfolio(
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
):
    user_id = payload.get("user_id", current_user.id)
    if user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return await portfolio_service.create(
        user_id=current_user.id,
        portfolio_name=payload.get("portfolio_name", "Default"),
        currency=payload.get("currency", "USDT"),
    )


@router.get("/snapshots", response_model=list[PortfolioSnapshotRead])
async def list_snapshots(
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
):
    portfolio = await portfolio_service.get_or_create_default(current_user.id)
    return await portfolio_service.list_snapshots(portfolio.id)


@router.post("/snapshots", response_model=PortfolioSnapshotRead, status_code=201)
async def create_snapshot(
    payload: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    portfolio_service: Annotated[PortfolioService, Depends(get_portfolio_service)],
):
    portfolio = await portfolio_service.get_or_create_default(current_user.id)
    portfolio_id = payload.get("portfolio_id", portfolio.id)
    if portfolio_id != portfolio.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return await portfolio_service.snapshot(
        portfolio_id=portfolio_id,
        total_value=payload.get("total_value", 0),
        cash_balance=payload.get("cash_balance", 0),
        open_positions=payload.get("open_positions", 0),
        daily_pnl=payload.get("daily_pnl", 0.0),
        total_pnl=payload.get("total_pnl", 0.0),
    )


@router.post("/analytics", response_model=PortfolioAnalyticsResponse)
async def calculate_portfolio_analytics(
    payload: PortfolioAnalyticsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
    redis_client=Depends(get_redis_client_optional),
):
    portfolio_service = PortfolioService(db)
    portfolio = await portfolio_service.get_or_create_default(current_user.id)

    date_from = (
        datetime.combine(payload.date_from, datetime.min.time()).replace(tzinfo=datetime.UTC)
        if payload.date_from
        else None
    )
    date_to = (
        datetime.combine(payload.date_to, datetime.max.time()).replace(tzinfo=datetime.UTC)
        if payload.date_to
        else None
    )

    analytics_service = PortfolioAnalyticsService(db, redis_client)
    metrics = analytics_service.calculate_portfolio_analytics(
        portfolio_id=payload.portfolio_id or portfolio.id,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        risk_free_rate=payload.risk_free_rate,
    )

    chart_data = {}
    snapshots = await portfolio_service.list_snapshots(portfolio.id, limit=100)
    chart_data["equity"] = [
        {"date": str(s.captured_at.date()), "value": float(s.total_value)}
        for s in sorted(snapshots, key=lambda s: s.captured_at)
    ]

    return PortfolioAnalyticsResponse(
        portfolio=PortfolioRead.model_validate(portfolio) if portfolio else None,
        metrics=PerformanceMetricsRead(
            total_return=metrics.total_return,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            calmar_ratio=metrics.calmar_ratio,
            profit_factor=metrics.profit_factor,
            win_rate=metrics.win_rate,
            expectancy=metrics.expectancy,
            max_drawdown=metrics.max_drawdown,
            risk_adjusted_return=metrics.risk_adjusted_return,
            period_start=metrics.period_start,
            period_end=metrics.period_end,
            total_trades=metrics.total_trades,
            winning_trades=metrics.winning_trades,
            losing_trades=metrics.losing_trades,
            gross_profit=metrics.gross_profit,
            gross_loss=metrics.gross_loss,
        ),
        chart_data=chart_data,
    )


@router.get("/analytics/history", response_model=list[PerformanceMetricsRead])
async def get_analytics_history(
    period_type: str | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db=Depends(get_db),
    redis_client=Depends(get_redis_client_optional),
):
    analytics_service = PortfolioAnalyticsService(db, redis_client)
    return await analytics_service.metrics_repo.get_by_user(current_user.id, period_type)
