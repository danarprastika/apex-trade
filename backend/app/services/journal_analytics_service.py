from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.database.repositories.journal_repository import TagRepository, TradeJournalRepository
from app.database.repositories.trading_repository import StrategyRepository, TradeRepository
from app.schemas.journal import JournalFilterParams


class JournalAnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.journals = TradeJournalRepository(db)
        self.tags = TagRepository(db)
        self.trades = TradeRepository(db)

    def get_performance_breakdown(
        self,
        user_id: str,
        filters: JournalFilterParams,
    ) -> dict[str, Any]:
        rows = self._journal_rows(user_id, filters)
        return {
            "overall": self._stats(rows),
            "by_strategy": self._group_stats(rows, "strategy_name"),
            "by_tag": self._group_stats(rows, "tags", multi=True),
            "by_risk_bucket": self._group_stats(rows, "risk_bucket"),
        }

    def get_risk_correlation(self, user_id: str, filters: JournalFilterParams) -> dict[str, Any]:
        rows = self._journal_rows(user_id, filters)
        points = [
            {
                "journal_id": row["journal_id"],
                "risk_score": row["risk_score"],
                "pnl": row["pnl"],
                "outcome": row["outcome"],
            }
            for row in rows
            if row["risk_score"] is not None
        ]
        return {
            "correlation": self._correlation(
                [point["risk_score"] for point in points],
                [point["pnl"] for point in points],
            ),
            "points": points,
        }

    def get_time_patterns(self, user_id: str, filters: JournalFilterParams) -> dict[str, Any]:
        rows = self._journal_rows(user_id, filters)
        by_hour = self._group_stats(rows, "hour")
        by_day_of_week = self._group_stats(rows, "day_of_week")
        return {"by_hour": by_hour, "by_day_of_week": by_day_of_week}

    def get_tag_efficacy(self, user_id: str, filters: JournalFilterParams) -> dict[str, Any]:
        rows = self._journal_rows(user_id, filters)
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            for tag in row["tags"]:
                grouped[tag].append(row)

        return {
            "items": [
                {
                    "tag": tag,
                    **self._stats(group_rows),
                }
                for tag, group_rows in sorted(grouped.items())
            ]
        }

    def _journal_rows(self, user_id: str, filters: JournalFilterParams) -> list[dict[str, Any]]:
        journals = self.journals.list_for_user_all(user_id, filters)
        strategy_names = {
            strategy.id: strategy.name
            for strategy in StrategyRepository(self.db).list(limit=10000)
        }
        rows: list[dict[str, Any]] = []

        for journal in journals:
            journal.tags = self.tags.get_by_names(journal.tags or [])
            trade = self.trades.get(journal.trade_id)
            pnl = float(trade.net_profit) if trade else 0.0
            opened_at = trade.opened_at if trade else journal.created_at
            tags = [tag.name for tag in journal.tags]
            rows.append(
                {
                    "journal_id": journal.id,
                    "trade_id": journal.trade_id,
                    "strategy_id": journal.strategy_id,
                    "strategy_name": strategy_names.get(journal.strategy_id, journal.strategy_id),
                    "tags": tags,
                    "risk_score": journal.risk_score,
                    "risk_bucket": self._risk_bucket(journal.risk_score),
                    "outcome": journal.outcome,
                    "pnl": pnl,
                    "hour": opened_at.hour if opened_at else None,
                    "day_of_week": opened_at.strftime("%A") if opened_at else None,
                }
            )

        return rows

    def _stats(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        profits = [float(row["pnl"]) for row in rows]
        risk_scores = [int(row["risk_score"]) for row in rows if row["risk_score"] is not None]
        wins = [profit for profit in profits if profit > 0]
        losses = [profit for profit in profits if profit < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        outcomes: dict[str, int] = defaultdict(int)
        for row in rows:
            outcomes[row["outcome"] or "UNKNOWN"] += 1

        return {
            "total_trades": len(rows),
            "win_rate": len(wins) / len(rows) if rows else None,
            "avg_pnl": sum(profits) / len(profits) if profits else None,
            "avg_profit": sum(profits) / len(profits) if profits else None,
            "profit_factor": gross_profit / gross_loss if gross_loss else None,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "avg_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else None,
            "by_outcome": dict(outcomes),
        }

    def _group_stats(
        self,
        rows: list[dict[str, Any]],
        key: str,
        multi: bool = False,
    ) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            values = row[key] if multi else [row[key]]
            for value in values or ["Unknown"]:
                grouped[str(value)].append(row)

        return {group: self._stats(group_rows) for group, group_rows in sorted(grouped.items())}

    def _correlation(self, xs: list[int | None], ys: list[float]) -> float | None:
        pairs = [(float(x), y) for x, y in zip(xs, ys, strict=False) if x is not None]
        if len(pairs) < 2:
            return None

        mean_x = sum(point[0] for point in pairs) / len(pairs)
        mean_y = sum(point[1] for point in pairs) / len(pairs)
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
        denominator_x = sum((x - mean_x) ** 2 for x, _ in pairs)
        denominator_y = sum((y - mean_y) ** 2 for _, y in pairs)
        denominator = (denominator_x * denominator_y) ** 0.5
        if denominator == 0:
            return None
        return numerator / denominator

    def _risk_bucket(self, risk_score: int | None) -> str:
        if risk_score is None:
            return "Unscored"
        if risk_score <= 3:
            return "Low Risk"
        if risk_score <= 7:
            return "Medium Risk"
        return "High Risk"
