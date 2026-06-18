from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PortfolioRead(BaseModel):
    id: str
    user_id: str
    portfolio_name: str
    currency: str
    total_value: float
    cash_balance: float
    risk_score: float
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PortfolioCreate(BaseModel):
    user_id: str
    portfolio_name: str = Field(default="Default", min_length=1, max_length=100)
    currency: str = Field(default="USDT", min_length=3, max_length=20)


class PortfolioSnapshotCreate(BaseModel):
    portfolio_id: str
    total_value: float = Field(ge=0)
    cash_balance: float = Field(ge=0)
    open_positions: int = Field(ge=0)
    daily_pnl: float = 0.0
    total_pnl: float = 0.0


class PortfolioSnapshotRead(BaseModel):
    id: int
    portfolio_id: str
    total_value: float
    cash_balance: float
    open_positions: int
    daily_pnl: float
    total_pnl: float
    captured_at: datetime

    model_config = {"from_attributes": True}


class PerformanceMetricsRead(BaseModel):
    total_return: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    calmar_ratio: float | None = None
    profit_factor: float | None = None
    win_rate: float | None = None
    expectancy: float | None = None
    max_drawdown: float | None = None
    risk_adjusted_return: float | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    gross_profit: float | None = None
    gross_loss: float | None = None


class PortfolioAnalyticsRequest(BaseModel):
    portfolio_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    risk_free_rate: float = 0.0


class PortfolioAnalyticsResponse(BaseModel):
    portfolio: PortfolioRead | None = None
    metrics: PerformanceMetricsRead
    chart_data: dict[str, list[dict[str, float | str]]] = {}
