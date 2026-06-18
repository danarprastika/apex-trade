from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class AnalyticsPeriod:
    period_type: str  # 'daily', 'weekly', 'monthly', 'all'
    date_from: date | None = None
    date_to: date | None = None

    @classmethod
    def from_dates(cls, date_from: date | None, date_to: date | None) -> AnalyticsPeriod:
        if date_from and date_to:
            days_diff = (date_to - date_from).days
            if days_diff <= 1:
                period_type = "daily"
            elif days_diff <= 7:
                period_type = "weekly"
            elif days_diff <= 31:
                period_type = "monthly"
            else:
                period_type = "all"
        else:
            period_type = "all"

        return cls(
            period_type=period_type,
            date_from=date_from,
            date_to=date_to,
        )


@dataclass
class PerformanceMetrics:
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
    volatility: float | None = None
    downside_deviation: float | None = None

    def to_dict(self) -> dict:
        return {
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "profit_factor": self.profit_factor,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "max_drawdown": self.max_drawdown,
            "risk_adjusted_return": self.risk_adjusted_return,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "gross_profit": self.gross_profit,
            "gross_loss": self.gross_loss,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PerformanceMetrics:
        return cls(**data)
