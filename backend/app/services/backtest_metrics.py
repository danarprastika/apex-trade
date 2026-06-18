from __future__ import annotations

import math
from datetime import datetime

from app.database.models.backtest import BacktestTrade
from app.schemas.backtest import BacktestMetricsRead


class BacktestMetricsCalculator:
    def __init__(self, trades: list[BacktestTrade], initial_capital: float, final_capital: float):
        self.trades = [t for t in trades if t.status == "CLOSED"]
        self.initial_capital = initial_capital
        self.final_capital = final_capital
        self.closed_trades = [t for t in self.trades if t.exit_price is not None and t.exit_time is not None]

    def calculate(self) -> BacktestMetricsRead:
        if not self.trades:
            return BacktestMetricsRead(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                net_profit=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                avg_trade_duration=0.0,
                total_commission=0.0,
                total_slippage=0.0,
            )

        winning = [t for t in self.trades if float(t.net_profit) > 0]
        losing = [t for t in self.trades if float(t.net_profit) <= 0]

        total_profit = sum(float(t.net_profit) for t in winning)
        total_loss = abs(sum(float(t.net_profit) for t in losing))
        net_profit = total_profit - total_loss

        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf") if total_profit > 0 else 0.0
        win_rate = len(winning) / len(self.trades) if self.trades else 0.0

        total_commission = sum(float(t.commission_cost) for t in self.trades)
        total_slippage = sum(float(t.slippage_cost) for t in self.trades)

        durations = []
        for t in self.closed_trades:
            if t.entry_time and t.exit_time:
                duration = (t.exit_time - t.entry_time).total_seconds() / 60
                durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        returns = [float(t.net_profit) / self.initial_capital for t in self.trades if self.initial_capital > 0]
        sharpe = self._sharpe_ratio(returns)
        sortino = self._sortino_ratio(returns)

        equity_curve = self._build_equity_curve()
        max_dd = self._max_drawdown(equity_curve)

        return BacktestMetricsRead(
            total_trades=len(self.trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=win_rate,
            gross_profit=total_profit,
            gross_loss=total_loss,
            net_profit=net_profit,
            profit_factor=profit_factor if profit_factor != float("inf") else 0.0,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            avg_trade_duration=avg_duration,
            total_commission=total_commission,
            total_slippage=total_slippage,
        )

    def _sharpe_ratio(self, returns: list[float]) -> float:
        if len(returns) < 2:
            return 0.0
        mean = sum(returns) / len(returns)
        std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
        return mean / std if std > 0 else 0.0

    def _sortino_ratio(self, returns: list[float]) -> float:
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        downside = [r for r in returns if r < 0]
        if not downside:
            return mean * 100 if mean > 0 else 0.0
        downside_std = math.sqrt(sum((r - mean) ** 2 for r in downside) / len(returns))
        return mean / downside_std if downside_std > 0 else 0.0

    def _build_equity_curve(self) -> list[tuple[datetime, float]]:
        curve = [(datetime.min, self.initial_capital)]
        capital = self.initial_capital
        sorted_trades = sorted(self.trades, key=lambda t: t.entry_time or datetime.min)
        for t in sorted_trades:
            capital += float(t.net_profit)
            if t.entry_time:
                curve.append((t.entry_time, capital))
        return curve

    def _max_drawdown(self, equity_curve: list[tuple[datetime, float]]) -> float:
        if not equity_curve:
            return 0.0
        peak = equity_curve[0][1]
        max_dd = 0.0
        for _, value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        return max_dd