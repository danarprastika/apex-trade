from __future__ import annotations

import hashlib
import logging

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.intelligence import FearGreedSnapshot, SentimentRecord, MarketRegimeSnapshot
from app.database.repositories.intelligence_repository import (
    FearGreedSnapshotRepository,
    SentimentRecordRepository,
    SentimentSourceRepository,
    MarketRegimeSnapshotRepository,
)

logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self, db: Session):
        self.db = db
        self.sources = SentimentSourceRepository(db)
        self.records = SentimentRecordRepository(db)

    def collect_sentiment(
        self,
        platform: str,
        text: str,
        text_hash: str | None = None,
        asset_symbols: list[str] | None = None,
    ) -> SentimentRecord | None:
        source = self.sources.find_one(source_name=platform)
        if not source:
            logger.warning("Unknown sentiment source: %s", platform)
            return None

        if text_hash is None:
            text_hash = self._compute_text_hash(text)

        existing = self.records.get_by_text_hash(text_hash)
        if existing:
            logger.info("Duplicate sentiment record ignored platform=%s", platform)
            return existing

        record = self.records.create(
            source_id=source.id,
            platform=platform,
            text_hash=text_hash,
            sentiment_score=0.0,
            confidence_score=0.5,
            mention_weight=1.0,
        )
        self.records.commit()
        self.records.refresh(record)
        return record

    def analyze_sentiment(
        self,
        record_id: int,
        sentiment_score: float,
        confidence_score: float,
        subjectivity_score: float | None = None,
        mention_weight: float = 1.0,
    ) -> SentimentRecord | None:
        record = self.records.get(record_id)
        if not record:
            return None

        self.records.update(
            record,
            sentiment_score=sentiment_score,
            confidence_score=confidence_score,
            subjectivity_score=subjectivity_score,
            mention_weight=mention_weight,
        )
        self.records.commit()
        return record

    def get_asset_sentiment(self, asset_id: str, lookback_minutes: int = 60) -> dict:
        cutoff = datetime.utcnow().replace(minute=datetime.utcnow().minute - lookback_minutes)
        records = self.db.scalars(
            select(SentimentRecord)
            .where(
                (SentimentRecord.asset_id == asset_id) &
                (SentimentRecord.confidence_score >= 0.5)
            )
            .order_by(SentimentRecord.collected_at.desc())
            .limit(1000)
        ).all()

        if not records:
            return {"sentiment_score": 0.0, "confidence": 0.0, "count": 0}

        total_weight = sum(r.mention_weight for r in records)
        weighted_score = sum(r.sentiment_score * r.mention_weight for r in records)
        avg_score = weighted_score / total_weight if total_weight > 0 else 0.0

        return {
            "sentiment_score": avg_score,
            "confidence": sum(r.confidence_score for r in records) / len(records),
            "count": len(records),
        }

    @staticmethod
    def _compute_text_hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:64]


class RegimeDetectionService:
    def __init__(self, db: Session):
        self.db = db
        self.snapshots = MarketRegimeSnapshotRepository(db)

    def detect_regime(
        self,
        market_pair_id: str | None = None,
        asset_id: str | None = None,
        timeframe: str = "1h",
        trend_strength: float = 0.0,
        volatility_score: float = 0.0,
        liquidity_score: float = 50.0,
    ) -> MarketRegimeSnapshot:
        regime = self._classify_regime(trend_strength, volatility_score, liquidity_score)
        confidence = self._compute_confidence(trend_strength, volatility_score, liquidity_score)

        snapshot = self.snapshots.create(
            market_pair_id=market_pair_id,
            asset_id=asset_id,
            timeframe=timeframe,
            regime=regime,
            confidence=confidence,
            trend_strength=trend_strength,
            volatility_score=volatility_score,
            liquidity_score=liquidity_score,
            features_json={
                "trend_strength": trend_strength,
                "volatility_score": volatility_score,
                "liquidity_score": liquidity_score,
            },
        )
        self.snapshots.commit()
        self.snapshots.refresh(snapshot)
        return snapshot

    def _classify_regime(self, trend_strength: float, volatility_score: float, liquidity_score: float) -> str:
        if liquidity_score < 30 or (trend_strength < 0 and volatility_score > 70):
            return "CRISIS"
        if volatility_score > 60:
            return "VOLATILE"
        if trend_strength > 50:
            return "TRENDING"
        return "SIDEWAYS"

    def _compute_confidence(self, trend_strength: float, volatility_score: float, liquidity_score: float) -> float:
        confidence = 0.0
        confidence += min(trend_strength, 100) * 0.3
        confidence += min(volatility_score, 100) * 0.3
        confidence += (100 - min(liquidity_score, 100)) * 0.4
        return min(confidence, 100.0)


class FearGreedService:
    def __init__(self, db: Session):
        self.db = db
        self.snapshots = FearGreedSnapshotRepository(db)

    def build_index(
        self,
        scope_type: str,
        scope_id: str,
        volatility_component: float = 50.0,
        trend_component: float = 50.0,
        volume_component: float = 50.0,
        sentiment_component: float = 50.0,
        news_component: float = 50.0,
    ) -> FearGreedSnapshot:
        index_value = (
            volatility_component * 0.2 +
            trend_component * 0.2 +
            volume_component * 0.2 +
            sentiment_component * 0.2 +
            news_component * 0.2
        )

        label = self._get_label(index_value)

        snapshot = self.snapshots.create(
            scope_type=scope_type,
            scope_id=scope_id,
            index_value=index_value,
            index_label=label,
            volatility_component=volatility_component,
            trend_component=trend_component,
            volume_component=volume_component,
            sentiment_component=sentiment_component,
            news_component=news_component,
            components_json={
                "volatility": volatility_component,
                "trend": trend_component,
                "volume": volume_component,
                "sentiment": sentiment_component,
                "news": news_component,
            },
        )
        self.snapshots.commit()
        self.snapshots.refresh(snapshot)
        return snapshot

    @staticmethod
    def _get_label(value: float) -> str:
        if value <= 20:
            return "Extreme Fear"
        if value <= 40:
            return "Fear"
        if value <= 60:
            return "Neutral"
        if value <= 80:
            return "Greed"
        return "Extreme Greed"