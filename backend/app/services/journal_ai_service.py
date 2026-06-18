from __future__ import annotations

from typing import Any

from app.database.models.journal import TradeJournal
from app.database.models.trading import Signal, Trade


class JournalAIService:
    MODEL_VERSION = "heuristic-v1"

    @staticmethod
    def build_enrichments(
        journal: TradeJournal,
        trade: Trade | None,
        signal: Signal | None,
    ) -> list[dict[str, Any]]:
        auto_tags = JournalAIService.build_auto_tags(journal, trade, signal)
        sentiment_flags = JournalAIService.build_sentiment_flags(journal, trade)
        behavioral_warnings = JournalAIService.build_behavioral_warnings(journal, trade)
        confidence = JournalAIService._calculate_confidence(
            auto_tags, sentiment_flags, behavioral_warnings
        )

        return [
            {
                "trade_journal_id": journal.id,
                "enrichment_type": "AUTO_TAGS",
                "payload": {"tags": auto_tags},
                "model_version": JournalAIService.MODEL_VERSION,
                "confidence": confidence,
            },
            {
                "trade_journal_id": journal.id,
                "enrichment_type": "SENTIMENT_FLAGS",
                "payload": sentiment_flags,
                "model_version": JournalAIService.MODEL_VERSION,
                "confidence": confidence,
            },
            {
                "trade_journal_id": journal.id,
                "enrichment_type": "BEHAVIORAL_WARNINGS",
                "payload": {"warnings": behavioral_warnings},
                "model_version": JournalAIService.MODEL_VERSION,
                "confidence": confidence,
            },
        ]

    @staticmethod
    def build_auto_tags(
        journal: TradeJournal,
        trade: Trade | None,
        signal: Signal | None,
    ) -> list[str]:
        tags: set[str] = set()
        text = " ".join(
            [
                journal.entry_reason or "",
                journal.exit_reason or "",
                journal.notes or "",
                journal.lessons_learned or "",
            ]
        ).lower()

        if trade is not None and trade.net_profit > 0:
            tags.add("winning-trade")
        if trade is not None and trade.net_profit < 0:
            tags.add("losing-trade")
        if trade is not None and trade.duration_minutes > 240:
            tags.add("long-duration")
        if trade is not None and trade.duration_minutes < 15:
            tags.add("scalp")
        if journal.risk_score and journal.risk_score >= 8:
            tags.add("high-risk")
        if signal and float(signal.confidence) >= 0.8:
            tags.add("high-confidence-signal")
        if "breakout" in text:
            tags.add("breakout")
        if "reversal" in text:
            tags.add("reversal")
        if "fomo" in text or "panic" in text:
            tags.add("emotional")
        if len((journal.notes or "").strip()) > 500:
            tags.add("detailed-review")

        return sorted(tags)

    @staticmethod
    def build_sentiment_flags(journal: TradeJournal, trade: Trade | None) -> dict[str, Any]:
        pnl = float(trade.net_profit) if trade else 0.0
        text = " ".join([journal.notes or "", journal.lessons_learned or ""]).lower()

        flags = {
            "pnl_sentiment": "positive" if pnl > 0 else "negative" if pnl < 0 else "neutral",
            "review_tone": "reflective" if len(text.split()) >= 25 else "brief",
            "discipline_flag": any(
                word in text for word in ["panic", "fomo", "revenge", "impulse"]
            ),
            "confidence_flag": bool(journal.risk_score and journal.risk_score <= 4 and pnl > 0),
        }
        return flags

    @staticmethod
    def build_behavioral_warnings(
        journal: TradeJournal,
        trade: Trade | None,
    ) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        pnl = float(trade.net_profit) if trade else 0.0
        text = " ".join([
            journal.entry_reason or "",
            journal.exit_reason or "",
            journal.notes or "",
        ]).lower()

        if journal.risk_score and journal.risk_score >= 8:
            warnings.append(
                {
                    "code": "HIGH_RISK_ENTRY",
                    "message": "This journal is tagged with a high risk score.",
                    "severity": "warning",
                }
            )
        if journal.risk_score and journal.risk_score >= 8 and pnl < 0:
            warnings.append(
                {
                    "code": "HIGH_RISK_LOSS",
                    "message": "A high-risk trade resulted in a loss.",
                    "severity": "high",
                }
            )
        if pnl < 0 and len((journal.lessons_learned or "").strip().split()) < 10:
            warnings.append(
                {
                    "code": "INSUFFICIENT_REVIEW",
                    "message": "Add more lessons learned after a losing trade.",
                    "severity": "medium",
                }
            )
        if any(word in text for word in ["fomo", "panic", "revenge", "impulse"]):
            warnings.append(
                {
                    "code": "EMOTIONAL_TRADE_SIGNAL",
                    "message": "Journal text contains emotional trading language.",
                    "severity": "high",
                }
            )

        return warnings

    @staticmethod
    def _calculate_confidence(
        auto_tags: list[str],
        sentiment_flags: dict[str, Any],
        behavioral_warnings: list[dict[str, Any]],
    ) -> float:
        signal_count = len(auto_tags) + sum(1 for value in sentiment_flags.values() if value)
        warning_penalty = min(0.2, len(behavioral_warnings) * 0.05)
        return max(0.1, min(0.95, 0.45 + signal_count * 0.08 - warning_penalty))
