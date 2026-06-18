from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_backtest_service, get_plugin_registry
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.database.models.identity import User
from app.schemas.backtest import BacktestConfigCreate, BacktestConfigRead, BacktestRunCreate, BacktestRunRead
from app.services.backtest_engine import BacktestEngine
from app.services.backtest_service import BacktestService
from app.services.plugin_registry import PluginRegistry

router = APIRouter()


@router.get("/backtest-configs", response_model=list[BacktestConfigRead])
async def list_configs(
    backtest_service: Annotated[BacktestService, Depends(get_backtest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return [BacktestConfigRead.model_validate(c) for c in await backtest_service.configs.list(limit=100)]


@router.post("/backtest-configs", response_model=BacktestConfigRead, status_code=201)
async def create_config(
    payload: BacktestConfigCreate,
    backtest_service: Annotated[BacktestService, Depends(get_backtest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {"TRADER", "ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    config = await backtest_service.create_config(
        strategy_id=payload.strategy_id,
        name=payload.name,
        position_sizing_method=payload.position_sizing_method.value,
        position_size_value=payload.position_size_value,
        max_positions=payload.max_positions,
        slippage_model=payload.slippage_model,
        commission_model=payload.commission_model,
    )
    return BacktestConfigRead.model_validate(config)


@router.get("/backtests", response_model=list[BacktestRunRead])
async def list_backtests(
    backtest_service: Annotated[BacktestService, Depends(get_backtest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return [BacktestRunRead.model_validate(r) for r in await backtest_service.list_runs(current_user.id)]


@router.post("/backtests", response_model=BacktestRunRead, status_code=201)
async def create_backtest(
    payload: BacktestRunCreate,
    backtest_service: Annotated[BacktestService, Depends(get_backtest_service)],
    registry: Annotated[PluginRegistry, Depends(get_plugin_registry)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in {"TRADER", "ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")

    run = await backtest_service.create_run(
        user_id=current_user.id,
        strategy_id=payload.strategy_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        initial_capital=payload.initial_capital,
        config_id=payload.config_id,
    )

    strategy = registry.get_plugin_by_strategy(payload.strategy_id)
    if strategy is None:
        raise NotFoundError("Strategy plugin not found")

    import asyncio

    engine = BacktestEngine(backtest_service.db, current_user.id)
    asyncio.create_task(
        engine.run_backtest(
            run_id=run.id,
            strategy_plugin=strategy,
            symbols=payload.symbols,
            timeframe=payload.timeframe,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            config={"position_sizing_method": "FIXED", "position_size_value": 0.01},
        )
    )

    return BacktestRunRead.model_validate(run)


@router.get("/backtests/{run_id}", response_model=BacktestRunRead)
async def get_backtest(
    run_id: str,
    backtest_service: Annotated[BacktestService, Depends(get_backtest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    run = await backtest_service.get_run(run_id)
    if run.user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Access denied")
    return BacktestRunRead.model_validate(run)


@router.delete("/backtests/{run_id}")
async def cancel_backtest(
    run_id: str,
    backtest_service: Annotated[BacktestService, Depends(get_backtest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    run = await backtest_service.get_run(run_id)
    if run.user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Access denied")
    await backtest_service.cancel_run(run_id)
    return {"status": "cancelled"}
