from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.intelligence import (
    FearGreedSnapshot,
    IntelligenceAlert,
    IntelligenceSnapshot,
    IntelligenceSource,
    MarketRegimeSnapshot,
    NewsArticle,
    NewsEvent,
    SentimentRecord,
    SentimentSource,
    SourceHealthMetric,
)
from app.database.repositories.base import BaseRepository


class IntelligenceSourceRepository(BaseRepository[IntelligenceSource]):
    def __init__(self, db: Session):
        super().__init__(db, IntelligenceSource)

    def get_by_name(self, source_name: str) -> IntelligenceSource | None:
        return self.db.scalar(select(IntelligenceSource).where(IntelligenceSource.source_name == source_name))

    def list_enabled(self, limit: int = 100, offset: int = 0) -> list[IntelligenceSource]:
        return list(
            self.db.scalars(
                select(IntelligenceSource)
                .where(IntelligenceSource.enabled.is_(True))
                .limit(limit)
                .offset(offset)
            ).all()
        )


class NewsArticleRepository(BaseRepository[NewsArticle]):
    def __init__(self, db: Session):
        super().__init__(db, NewsArticle)

    def get_by_dedupe_hash(self, dedupe_hash: str) -> NewsArticle | None:
        return self.db.scalar(select(NewsArticle).where(NewsArticle.dedupe_hash == dedupe_hash))

    def get_latest_for_asset(self, asset_id: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(NewsArticle)
                .where(NewsArticle.asset_id == asset_id)
                .order_by(NewsArticle.published_at.desc())
                .limit(limit)
            ).all()
        )

    def get_latest_for_pair(self, market_pair_id: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(NewsArticle)
                .where(NewsArticle.market_pair_id == market_pair_id)
                .order_by(NewsArticle.published_at.desc())
                .limit(limit)
            ).all()
        )


class NewsEventRepository(BaseRepository[NewsEvent]):
    def __init__(self, db: Session):
        super().__init__(db, NewsEvent)

    def get_by_event_type(self, event_type: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(NewsEvent)
                .where(NewsEvent.event_type == event_type)
                .order_by(NewsEvent.detected_at.desc())
                .limit(limit)
            ).all()
        )


class SentimentSourceRepository(BaseRepository[SentimentSource]):
    def __init__(self, db: Session):
        super().__init__(db, SentimentSource)

    def list_enabled(self, limit: int = 100) -> list[SentimentSource]:
        return list(
            self.db.scalars(
                select(SentimentSource).where(SentimentSource.enabled.is_(True)).limit(limit)
            ).all()
        )


class SentimentRecordRepository(BaseRepository[SentimentRecord]):
    def __init__(self, db: Session):
        super().__init__(db, SentimentRecord)

    def get_latest_for_asset(self, asset_id: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(SentimentRecord)
                .where(SentimentRecord.asset_id == asset_id)
                .order_by(SentimentRecord.collected_at.desc())
                .limit(limit)
            ).all()
        )

    def get_by_text_hash(self, text_hash: str) -> SentimentRecord | None:
        return self.db.scalar(select(SentimentRecord).where(SentimentRecord.text_hash == text_hash))


class FearGreedSnapshotRepository(BaseRepository[FearGreedSnapshot]):
    def __init__(self, db: Session):
        super().__init__(db, FearGreedSnapshot)

    def get_latest_for_scope(self, scope_type: str, scope_id: str):
        return self.db.scalar(
            select(FearGreedSnapshot)
            .where((FearGreedSnapshot.scope_type == scope_type) & (FearGreedSnapshot.scope_id == scope_id))
            .order_by(FearGreedSnapshot.captured_at.desc())
        )

    def get_history_for_scope(self, scope_type: str, scope_id: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(FearGreedSnapshot)
                .where((FearGreedSnapshot.scope_type == scope_type) & (FearGreedSnapshot.scope_id == scope_id))
                .order_by(FearGreedSnapshot.captured_at.desc())
                .limit(limit)
            ).all()
        )


class MarketRegimeSnapshotRepository(BaseRepository[MarketRegimeSnapshot]):
    def __init__(self, db: Session):
        super().__init__(db, MarketRegimeSnapshot)

    def get_latest_for_pair(self, market_pair_id: str, timeframe: str = "1h"):
        return self.db.scalar(
            select(MarketRegimeSnapshot)
            .where(
                (MarketRegimeSnapshot.market_pair_id == market_pair_id)
                & (MarketRegimeSnapshot.timeframe == timeframe)
            )
            .order_by(MarketRegimeSnapshot.detected_at.desc())
        )

    def get_history_for_pair(self, market_pair_id: str, timeframe: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(MarketRegimeSnapshot)
                .where(
                    (MarketRegimeSnapshot.market_pair_id == market_pair_id)
                    & (MarketRegimeSnapshot.timeframe == timeframe)
                )
                .order_by(MarketRegimeSnapshot.detected_at.desc())
                .limit(limit)
            ).all()
        )


class IntelligenceSnapshotRepository(BaseRepository[IntelligenceSnapshot]):
    def __init__(self, db: Session):
        super().__init__(db, IntelligenceSnapshot)

    def get_latest_for_asset(self, asset_id: str):
        return self.db.scalar(
            select(IntelligenceSnapshot)
            .where(IntelligenceSnapshot.asset_id == asset_id)
            .order_by(IntelligenceSnapshot.generated_at.desc())
        )

    def get_latest_for_pair(self, market_pair_id: str):
        return self.db.scalar(
            select(IntelligenceSnapshot)
            .where(IntelligenceSnapshot.market_pair_id == market_pair_id)
            .order_by(IntelligenceSnapshot.generated_at.desc())
        )


class IntelligenceAlertRepository(BaseRepository[IntelligenceAlert]):
    def __init__(self, db: Session):
        super().__init__(db, IntelligenceAlert)

    def get_active(self, limit: int = 100):
        return list(
            self.db.scalars(
                select(IntelligenceAlert)
                .where(IntelligenceAlert.status == "ACTIVE")
                .order_by(IntelligenceAlert.created_at.desc())
                .limit(limit)
            ).all()
        )

    def get_by_severity(self, severity: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(IntelligenceAlert)
                .where(IntelligenceAlert.severity == severity)
                .order_by(IntelligenceAlert.created_at.desc())
                .limit(limit)
            ).all()
        )


class SourceHealthMetricRepository(BaseRepository[SourceHealthMetric]):
    def __init__(self, db: Session):
        super().__init__(db, SourceHealthMetric)

    def get_latest_for_source(self, source_id: str):
        return self.db.scalar(
            select(SourceHealthMetric)
            .where(SourceHealthMetric.source_id == source_id)
            .order_by(SourceHealthMetric.last_attempt_at.desc())
        )