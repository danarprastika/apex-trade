from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BacktestStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PositionSizingMethod(str, Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"
    RISK_BASED = "RISK_BASED"


class SlippageModelType(str, Enum):
    FIXED = "FIXED"
    VOLUME_BASED = "VOLUME_BASED"
    VOLATILITY_BASED = "VOLATILITY_BASED"
    HISTORICAL = "HISTORICAL"


class CommissionModelType(str, Enum):
    FLAT = "FLAT"
    EXCHANGE_TIER = "EXCHANGE_TIER"


class BacktestConfigCreate(BaseModel):
    strategy_id: str
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    position_sizing_method: PositionSizingMethod = PositionSizingMethod.FIXED
    position_size_value: float = Field(gt=0)
    max_positions: int = Field(ge=1, default=5)
    slippage_model: dict
    commission_model: dict


class BacktestConfigUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    position_sizing_method: PositionSizingMethod | None = None
    position_size_value: float | None = None
    max_positions: int | None = None
    slippage_model: dict | None = None
    commission_model: dict | None = None


class BacktestConfigRead(BaseModel):
    id: str
    strategy_id: str
    name: str
    description: str | None
    position_sizing_method: str
    position_size_value: float
    max_positions: int
    slippage_model: dict
    commission_model: dict
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BacktestRunCreate(BaseModel):
    strategy_id: str
    config_id: str | None = None
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    symbols: list[str]
    timeframe: str = Field(min_length=1, max_length=10)
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(gt=0)


class BacktestRunRead(BaseModel):
    id: str
    user_id: str
    strategy_id: str
    config_id: str | None
    name: str
    description: str | None
    status: str
    progress: float
    initial_capital: float
    final_capital: float | None
    total_trades: int
    start_date: datetime
    end_date: datetime
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class BacktestRunUpdate(BaseModel):
    status: BacktestStatus | None = None
    progress: float | None = None
    error_details: str | None = None


class BacktestSessionRead(BaseModel):
    id: str
    backtest_run_id: str
    market_pair_id: str
    timeframe: str
    candle_count: int
    status: str
    start_time: datetime
    end_time: datetime

    model_config = {"from_attributes": True}


class BacktestTradeRead(BaseModel):
    id: str
    backtest_run_id: str
    symbol: str
    entry_price: float
    exit_price: float | None
    quantity: float
    entry_time: datetime
    exit_time: datetime | None
    gross_profit: float
    commission_cost: float
    slippage_cost: float
    net_profit: float
    status: str

    model_config = {"from_attributes": True}


class BacktestMetricsRead(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    avg_trade_duration: float
    total_commission: float
    total_slippage: float

    model_config = {"from_attributes": True}


class EquityPoint(BaseModel):
    timestamp: datetime
    capital: float


class EquityCurve(BaseModel):
    points: list[EquityPoint]


class BacktestReport(BaseModel):
    run: BacktestRunRead
    metrics: BacktestMetricsRead
    equity_curve: list[EquityPoint]
    trades: list[BacktestTradeRead]