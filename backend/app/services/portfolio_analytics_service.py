from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.portfolio import PortfolioSnapshot
from app.database.models.trading import Position, Trade
from app.database.repositories.analytics_repository import PerformanceMetricsRepository
from app.database.repositories.portfolio_repository import PortfolioSnapshotRepository
from app.database.repositories.trading_repository import TradeRepository
from app.domain.analytics.value_objects import AnalyticsPeriod, PerformanceMetrics
from app.integrations.redis.client import RedisClient

logger = logging.getLogger(__name__)


class PortfolioAnalyticsService:
    TRADING_DAYS_PER_YEAR = 252
    DEFAULT_RISK_FREE_RATE = 0.0

    def __init__(self, db: Session, redis_client: RedisClient | None = None):
        self.db = db
        self.trades = TradeRepository(db)
        self.snapshots = PortfolioSnapshotRepository(db)
        self.metrics_repo = PerformanceMetricsRepository(db)
        self.redis = redis_client

    def calculate_portfolio_analytics(
        self,
        portfolio_id: str,
        user_id: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    ) -> PerformanceMetrics:
        period = AnalyticsPeriod.from_dates(
            date_from.date() if date_from else None,
            date_to.date() if date_to else None,
        )

        cache_key = f"analytics:{portfolio_id}:{period.period_type}"
        if self.redis:
            try:
                cached = self.redis.client.get(cache_key)
                if cached:
                    import json
                    return PerformanceMetrics.from_dict(json.loads(cached))
            except Exception:
                pass

        snapshots = self._get_snapshots(portfolio_id, date_from, date_to)
        trades = self._get_trades(portfolio_id, date_from, date_to)

        metrics = self._calculate_all_metrics(snapshots, trades, risk_free_rate)

        if self.redis:
            try:
                import json
                self.redis.client.set(cache_key, json.dumps(metrics.to_dict()), ex=300)
            except Exception:
                pass

        return metrics

    def _get_snapshots(
        self,
        portfolio_id: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[PortfolioSnapshot]:
        stmt = select(PortfolioSnapshot).where(
            PortfolioSnapshot.portfolio_id == portfolio_id
        )
        if date_from:
            stmt = stmt.where(PortfolioSnapshot.captured_at >= date_from)
        if date_to:
            stmt = stmt.where(PortfolioSnapshot.captured_at <= date_to)
        return list(self.db.scalars(stmt.order_by(PortfolioSnapshot.captured_at)).all())

    def _get_trades(
        self,
        portfolio_id: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Trade]:
        stmt = (
            select(Trade)
            .join(Position, Trade.position_id == Position.id)
            .where(Position.portfolio_id == portfolio_id)
        )
        if date_from:
            stmt = stmt.where(Trade.opened_at >= date_from)
        if date_to:
            stmt = stmt.where(Trade.closed_at <= date_to)
        return list(self.db.scalars(stmt.order_by(Trade.opened_at)).all())

    def _calculate_all_metrics(
        self,
        snapshots: list[Any],
        trades: list[Trade],
        risk_free_rate: float,
    ) -> PerformanceMetrics:
        if not snapshots:
            return PerformanceMetrics()

        returns = self._calculate_returns_series(snapshots)

        total_return = self._calculate_total_return(snapshots)
        sharpe_ratio = self._calculate_sharpe_ratio(returns, risk_free_rate)
        sortino_ratio = self._calculate_sortino_ratio(returns, risk_free_rate)
        max_drawdown = self._calculate_max_drawdown(snapshots)
        calmar_ratio = self._calculate_calmar_ratio(total_return, max_drawdown)
        risk_adjusted_return = self._calculate_risk_adjusted_return(total_return, returns)

        trade_stats = self._calculate_trade_statistics(trades)
        profit_factor = self._calculate_profit_factor(trade_stats["gross_profit"], trade_stats["gross_loss"])
        win_rate = self._calculate_win_rate(trade_stats["winning_trades"], trade_stats["total_trades"])
        expectancy = self._calculate_expectancy(
            win_rate, trade_stats["avg_win"], trade_stats["avg_loss"]
        )

        period_start = min(s.captured_at for s in snapshots) if snapshots else None
        period_end = max(s.captured_at for s in snapshots) if snapshots else None

        return PerformanceMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            profit_factor=profit_factor,
            win_rate=win_rate,
            expectancy=expectancy,
            max_drawdown=max_drawdown,
            risk_adjusted_return=risk_adjusted_return,
            period_start=period_start,
            period_end=period_end,
            total_trades=trade_stats["total_trades"],
            winning_trades=trade_stats["winning_trades"],
            losing_trades=trade_stats["losing_trades"],
            gross_profit=trade_stats["gross_profit"],
            gross_loss=trade_stats["gross_loss"],
            volatility=trade_stats["volatility"],
            downside_deviation=trade_stats["downside_deviation"],
        )

    def _calculate_returns_series(self, snapshots: list[Any]) -> list[float]:
        if len(snapshots) < 2:
            return []

        sorted_snapshots = sorted(snapshots, key=lambda s: s.captured_at)
        returns = []

        for i in range(1, len(sorted_snapshots)):
            prev_value = float(sorted_snapshots[i - 1].total_value)
            curr_value = float(sorted_snapshots[i].total_value)
            if prev_value > 0:
                returns.append((curr_value - prev_value) / prev_value)

        return returns

    def _calculate_total_return(self, snapshots: list[Any]) -> float | None:
        if len(snapshots) < 2:
            return None

        sorted_snapshots = sorted(snapshots, key=lambda s: s.captured_at)
        initial = float(sorted_snapshots[0].total_value)
        final = float(sorted_snapshots[-1].total_value)

        if initial <= 0:
            return None

        return (final - initial) / initial

    def _calculate_sharpe_ratio(
        self, returns: list[float], risk_free_rate: float
    ) -> float | None:
        if len(returns) < 2:
            return None

        mean_return = sum(returns) / len(returns)
        std_dev = self._calculate_std_dev(returns, mean_return)

        if std_dev == 0 or math.isnan(std_dev):
            return None

        excess_return = mean_return - (risk_free_rate / self.TRADING_DAYS_PER_YEAR)
        annualized_excess = excess_return * math.sqrt(self.TRADING_DAYS_PER_YEAR)

        return annualized_excess / std_dev

    def _calculate_sortino_ratio(
        self, returns: list[float], risk_free_rate: float
    ) -> float | None:
        if len(returns) < 2:
            return None

        mean_return = sum(returns) / len(returns)
        downside_dev = self._calculate_downside_deviation(returns, risk_free_rate / self.TRADING_DAYS_PER_YEAR)

        if downside_dev == 0 or math.isnan(downside_dev):
            return None

        target_return = risk_free_rate / self.TRADING_DAYS_PER_YEAR
        excess_return = mean_return - target_return
        annualized_excess = excess_return * math.sqrt(self.TRADING_DAYS_PER_YEAR)

        return annualized_excess / downside_dev

    def _calculate_std_dev(self, values: list[float], mean: float) -> float:
        if len(values) < 2:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)

    def _calculate_downside_deviation(
        self, returns: list[float], target_return: float
    ) -> float:
        downside_returns = [r for r in returns if r < target_return]
        if len(downside_returns) < 2:
            return 0.0

        return math.sqrt(sum((r - target_return) ** 2 for r in downside_returns) / len(downside_returns))

    def _calculate_max_drawdown(self, snapshots: list[Any]) -> float | None:
        if len(snapshots) < 2:
            return None

        sorted_snapshots = sorted(snapshots, key=lambda s: s.captured_at)
        peak = float(sorted_snapshots[0].total_value)
        max_dd = 0.0

        for snapshot in sorted_snapshots[1:]:
            value = float(snapshot.total_value)
            if value > peak:
                peak = value
            elif peak > 0:
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd

        return max_dd if max_dd > 0 else None

    def _calculate_calmar_ratio(
        self, total_return: float | None, max_drawdown: float | None
    ) -> float | None:
        if total_return is None or max_drawdown is None or max_drawdown == 0:
            return None
        annualized_return = total_return * self.TRADING_DAYS_PER_YEAR
        return abs(annualized_return) / abs(max_drawdown)

    def _calculate_risk_adjusted_return(
        self, total_return: float | None, returns: list[float]
    ) -> float | None:
        if total_return is None or len(returns) < 2:
            return None

        std_dev = self._calculate_std_dev(returns, sum(returns) / len(returns))
        if std_dev == 0 or math.isnan(std_dev):
            return None

        return total_return / std_dev

    def _calculate_trade_statistics(self, trades: list[Trade]) -> dict[str, Any]:
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "volatility": None,
                "downside_deviation": None,
            }

        winning = [t for t in trades if float(t.net_profit) > 0]
        losing = [t for t in trades if float(t.net_profit) <= 0]

        gross_profit = sum(float(t.net_profit) for t in winning)
        gross_loss = abs(sum(float(t.net_profit) for t in losing))

        avg_win = gross_profit / len(winning) if winning else 0.0
        avg_loss = gross_loss / len(losing) if losing else 0.0

        profits = [float(t.net_profit) for t in trades]
        mean_profit = sum(profits) / len(profits)
        variance = sum((p - mean_profit) ** 2 for p in profits) / len(profits) if len(profits) > 1 else 0
        volatility = math.sqrt(variance)

        downside_dev = self._calculate_downside_deviation([float(t.net_profit) for t in trades], 0)

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "volatility": volatility,
            "downside_deviation": downside_dev,
        }

    def _calculate_profit_factor(
        self, gross_profit: float | None, gross_loss: float | None
    ) -> float | None:
        if gross_profit is None or gross_loss is None or gross_loss == 0:
            return None
        if gross_profit == 0:
            return 0.0
        return gross_profit / gross_loss

    def _calculate_win_rate(
        self, winning_trades: int, total_trades: int
    ) -> float | None:
        if total_trades == 0:
            return None
        return winning_trades / total_trades

    def _calculate_expectancy(
        self, win_rate: float | None, avg_win: float, avg_loss: float
    ) -> float | None:
        if win_rate is None:
            return None
        loss_rate = 1 - win_rate
        return win_rate * avg_win - loss_rate * avg_loss

    def persist_metrics(
        self,
        portfolio_id: str,
        user_id: str,
        date_from: datetime,
        date_to: datetime,
        period_type: str,
        metrics: PerformanceMetrics,
    ) -> None:
        self.metrics_repo.create_or_update(
            portfolio_id=portfolio_id,
            user_id=user_id,
            period_start=date_from,
            period_end=date_to,
            period_type=period_type,
            metrics={
                "total_return": metrics.total_return,
                "sharpe_ratio": metrics.sharpe_ratio,
                "sortino_ratio": metrics.sortino_ratio,
                "calmar_ratio": metrics.calmar_ratio,
                "profit_factor": metrics.profit_factor,
                "win_rate": metrics.win_rate,
                "expectancy": metrics.expectancy,
                "max_drawdown": metrics.max_drawdown,
                "risk_adjusted_return": metrics.risk_adjusted_return,
                "total_trades": metrics.total_trades,
                "winning_trades": metrics.winning_trades,
                "losing_trades": metrics.losing_trades,
                "gross_profit": metrics.gross_profit,
                "gross_loss": metrics.gross_loss,
                "volatility": metrics.volatility,
                "downside_deviation": metrics.downside_deviation,
            },
        )
        self.db.commit()
