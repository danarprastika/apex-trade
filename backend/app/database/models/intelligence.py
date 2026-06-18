from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class IntelligenceSource(Base, TimestampMixin):
    __tablename__ = "intelligence_sources"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    reliability_score: Mapped[float] = mapped_column(default=50.0, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(default=60, nullable=False)
    auth_required: Mapped[bool] = mapped_column(default=False, nullable=False)


class NewsArticle(Base, TimestampMixin):
    __tablename__ = "news_articles"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("intelligence_sources.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    sentiment_polarity: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    sentiment_score: Mapped[float] = mapped_column(nullable=True)
    impact_score: Mapped[float] = mapped_column(nullable=True, index=True)
    reliability_score: Mapped[float] = mapped_column(default=50.0, nullable=False)
    published_at: Mapped[datetime] = mapped_column(nullable=True, index=True)
    collected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)
    dedupe_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)


class NewsEvent(Base, TimestampMixin):
    __tablename__ = "news_events"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    article_id: Mapped[str] = mapped_column(ForeignKey("news_articles.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[int] = mapped_column(nullable=False, index=True)
    impact_score: Mapped[float] = mapped_column(nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    detected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)
    explanation: Mapped[str] = mapped_column(String(2000), nullable=True)


class SentimentSource(Base, TimestampMixin):
    __tablename__ = "sentiment_sources"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(default=60, nullable=False)
    reliability_score: Mapped[float] = mapped_column(default=50.0, nullable=False)
    allowed_keywords: Mapped[list] = mapped_column(JSON, nullable=True)


class SentimentRecord(Base, TimestampMixin):
    __tablename__ = "sentiment_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sentiment_sources.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sentiment_score: Mapped[float] = mapped_column(nullable=False)
    confidence_score: Mapped[float] = mapped_column(nullable=False)
    subjectivity_score: Mapped[float] = mapped_column(nullable=True)
    mention_weight: Mapped[float] = mapped_column(default=1.0, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)


class FearGreedSnapshot(Base, TimestampMixin):
    __tablename__ = "fear_greed_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_id: Mapped[str] = mapped_column(String(100), nullable=False)
    index_value: Mapped[float] = mapped_column(nullable=False)
    index_label: Mapped[str] = mapped_column(String(30), nullable=False)
    volatility_component: Mapped[float] = mapped_column(nullable=True)
    trend_component: Mapped[float] = mapped_column(nullable=True)
    volume_component: Mapped[float] = mapped_column(nullable=True)
    sentiment_component: Mapped[float] = mapped_column(nullable=True)
    news_component: Mapped[float] = mapped_column(nullable=True)
    components_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)


class MarketRegimeSnapshot(Base, TimestampMixin):
    __tablename__ = "market_regime_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), nullable=True, index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    regime: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    trend_strength: Mapped[float] = mapped_column(nullable=True)
    volatility_score: Mapped[float] = mapped_column(nullable=True)
    liquidity_score: Mapped[float] = mapped_column(nullable=True)
    features_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)


class IntelligenceSnapshot(Base, TimestampMixin):
    __tablename__ = "intelligence_snapshots"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), nullable=True, index=True)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=True, index=True)
    intelligence_score: Mapped[float] = mapped_column(nullable=False, default=50.0, index=True)
    news_score: Mapped[float] = mapped_column(nullable=True)
    social_sentiment_score: Mapped[float] = mapped_column(nullable=True)
    market_sentiment_score: Mapped[float] = mapped_column(nullable=True)
    fear_greed_index: Mapped[float] = mapped_column(nullable=True)
    regime: Mapped[str] = mapped_column(String(30), nullable=True)
    regime_confidence: Mapped[float] = mapped_column(nullable=True)
    overall_confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    risk_modifier: Mapped[float] = mapped_column(default=0.0, nullable=False)
    explanation: Mapped[str] = mapped_column(String(2000), nullable=True)
    components_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)


class IntelligenceAlert(Base, TimestampMixin):
    __tablename__ = "intelligence_alerts"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), nullable=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    trigger_snapshot_id: Mapped[str] = mapped_column(ForeignKey("intelligence_snapshots.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False, index=True)
    resolved_at: Mapped[datetime] = mapped_column(nullable=True)


class SourceHealthMetric(Base):
    __tablename__ = "source_health_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("intelligence_sources.id"), nullable=False, index=True)
    success_rate: Mapped[float] = mapped_column(nullable=False, default=100.0)
    latency_ms: Mapped[float] = mapped_column(nullable=True)
    freshness_seconds: Mapped[int] = mapped_column(nullable=True)
    error_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_success_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=True)
    last_attempt_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=True)