from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models.intelligence import IntelligenceAlert, IntelligenceSnapshot
from app.database.repositories.intelligence_repository import (
    FearGreedSnapshotRepository,
    IntelligenceAlertRepository,
    IntelligenceSnapshotRepository,
    MarketRegimeSnapshotRepository,
    NewsArticleRepository,
    SentimentRecordRepository,
)

logger = logging.getLogger(__name__)


class IntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        self.snapshots = IntelligenceSnapshotRepository(db)
        self.alerts = IntelligenceAlertRepository(db)
        self.news = NewsArticleRepository(db)
        self.sentiment = SentimentRecordRepository(db)
        self.regimes = MarketRegimeSnapshotRepository(db)
        self.fear_greed = FearGreedSnapshotRepository(db)

    def build_snapshot(
        self,
        asset_id: str | None = None,
        market_pair_id: str | None = None,
        scope_type: str = "ASSET",
        timeframe: str = "1h",
    ) -> IntelligenceSnapshot:
        news_score = self._compute_news_score(asset_id)
        social_score = self._compute_sentiment_score(asset_id)
        market_sentiment_score = self._compute_market_sentiment_score()
        fear_greed = self._get_fear_greed(scope_type, asset_id or "global")

        intelligence_score = (
            (news_score or 50) * 0.3 +
            (social_score or 50) * 0.3 +
            (market_sentiment_score or 50) * 0.2 +
            (fear_greed or 50) * 0.2
        )

        regime = self._get_regime(market_pair_id, timeframe)

        confidence = self._compute_confidence(news_score, social_score, market_sentiment_score, fear_greed)

        snapshot = self.snapshots.create(
            asset_id=asset_id,
            market_pair_id=market_pair_id,
            scope_type=scope_type,
            timeframe=timeframe,
            intelligence_score=intelligence_score,
            news_score=news_score,
            social_sentiment_score=social_score,
            market_sentiment_score=market_sentiment_score,
            fear_greed_index=fear_greed,
            regime=regime,
            regime_confidence=50.0,
            overall_confidence=confidence,
            risk_modifier=0.0,
            explanation=self._build_explanation(intelligence_score, regime),
            components_json={
                "news": news_score,
                "social": social_score,
                "market_sentiment": market_sentiment_score,
                "fear_greed": fear_greed,
            },
        )
        self.snapshots.commit()
        self.snapshots.refresh(snapshot)
        return snapshot

    def _compute_news_score(self, asset_id: str | None) -> float:
        if not asset_id:
            return 50.0
        articles = list(self.news.get_latest_for_asset(asset_id, limit=50))
        if not articles:
            return 50.0
        scores = [a.impact_score for a in articles if a.impact_score]
        return sum(scores) / len(scores) if scores else 50.0

    def _compute_sentiment_score(self, asset_id: str | None) -> float:
        if not asset_id:
            return 50.0
        records = list(self.sentiment.get_latest_for_asset(asset_id, limit=50))
        if not records:
            return 50.0
        scores = [r.sentiment_score for r in records if r.sentiment_score]
        return sum(scores) / len(scores) if scores else 50.0

    def _compute_market_sentiment_score(self) -> float:
        return 50.0

    def _get_fear_greed(self, scope_type: str, scope_id: str) -> float:
        snapshot = self.fear_greed.get_latest_for_scope(scope_type, scope_id)
        return snapshot.index_value if snapshot else 50.0

    def _get_regime(self, market_pair_id: str | None, timeframe: str) -> str | None:
        if not market_pair_id:
            return None
        snapshot = self.regimes.get_latest_for_pair(market_pair_id, timeframe)
        return snapshot.regime if snapshot else "SIDEWAYS"

    def _compute_confidence(
        self,
        news_score: float | None,
        social_score: float | None,
        market_score: float | None,
        fear_greed: float | None,
    ) -> float:
        available = [s for s in [news_score, social_score, market_score, fear_greed] if s is not None]
        return sum(available) / len(available) if available else 0.0

    def _build_explanation(self, intelligence_score: float, regime: str | None) -> str:
        if regime == "CRISIS":
            return "Crisis regime detected - high caution advised"
        if regime == "VOLATILE":
            return "Volatile market conditions detected"
        if regime == "TRENDING":
            return "Market in trending regime"
        return "Market regime stable - monitoring continues"

    def check_alert_policy(
        self,
        snapshot: IntelligenceSnapshot,
        previous_snapshot: IntelligenceSnapshot | None = None,
    ) -> IntelligenceAlert | None:
        if snapshot.intelligence_score < 20:
            return self.alerts.create(
                asset_id=snapshot.asset_id,
                market_pair_id=snapshot.market_pair_id,
                alert_type="EXTREME_FEAR",
                severity="HIGH",
                title="Extreme Fear Detected",
                message=f"Intelligence score dropped to {snapshot.intelligence_score}",
                status="ACTIVE",
            )
        if snapshot.intelligence_score > 80:
            return self.alerts.create(
                asset_id=snapshot.asset_id,
                market_pair_id=snapshot.market_pair_id,
                alert_type="EXTREME_GREED",
                severity="MEDIUM",
                title="Extreme Greed Detected",
                message=f"Intelligence score rose to {snapshot.intelligence_score}",
                status="ACTIVE",
            )
        if snapshot.regime == "CRISIS" and previous_snapshot and previous_snapshot.regime != "CRISIS":
            return self.alerts.create(
                asset_id=snapshot.asset_id,
                market_pair_id=snapshot.market_pair_id,
                alert_type="CRISIS_REGIME",
                severity="HIGH",
                title="Crisis Regime Detected",
                message="Market has entered crisis regime",
                status="ACTIVE",
            )
        return None