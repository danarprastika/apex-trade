from __future__ import annotations

from datetime import datetime

from app.database.models.backtest import BacktestRun, BacktestTrade
from app.schemas.backtest import BacktestMetricsRead, BacktestReport, EquityPoint, EquityCurve
from app.services.backtest_metrics import BacktestMetricsCalculator


class BacktestReportGenerator:
    def generate_report(
        self,
        run: BacktestRun,
        metrics: BacktestMetricsRead,
        trades: list[BacktestTrade],
    ) -> BacktestReport:
        equity_curve = self._build_equity_curve(trades, run.initial_capital)
        return BacktestReport(
            run=run,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades,
        )

    def _build_equity_curve(self, trades: list[BacktestTrade], initial_capital: float) -> list[EquityPoint]:
        closed_trades = sorted(
            [t for t in trades if t.status == "CLOSED" and t.exit_time],
            key=lambda t: t.exit_time,
        )

        points = [EquityPoint(timestamp=datetime.min, capital=initial_capital)]
        capital = initial_capital
        for trade in closed_trades:
            capital += float(trade.net_profit)
            points.append(EquityPoint(timestamp=trade.exit_time, capital=capital))
        return points

    def to_html(self, report: BacktestReport) -> str:
        return f"""<!DOCTYPE html>
<html>
<head><title>Backtest Report - {report.run.name}</title></head>
<body>
<h1>{report.run.name}</h1>
<p>Status: {report.run.status}</p>
<p>Total Trades: {report.metrics.total_trades}</p>
<p>Net Profit: {report.metrics.net_profit:.2f}</p>
<p>Win Rate: {report.metrics.win_rate:.2%}</p>
</body>
</html>"""