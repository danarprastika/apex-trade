from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IntelligenceSourceRead(BaseModel):
    id: str
    source_name: str
    source_type: str
    category: str
    url: str | None = None
    enabled: bool
    reliability_score: float
    rate_limit_per_minute: int
    auth_required: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntelligenceSourceCreate(BaseModel):
    source_name: str = Field(min_length=1, max_length=100)
    source_type: str = Field(min_length=1, max_length=30)
    category: str = Field(min_length=1, max_length=50)
    url: str | None = None
    enabled: bool = True
    reliability_score: float = Field(default=50.0, ge=0, le=100)
    rate_limit_per_minute: int = Field(default=60, gt=0)
    auth_required: bool = False


class IntelligenceSourceUpdate(BaseModel):
    source_name: str | None = None
    source_type: str | None = None
    category: str | None = None
    url: str | None = None
    enabled: bool | None = None
    reliability_score: float | None = Field(default=None, ge=0, le=100)
    rate_limit_per_minute: int | None = Field(default=None, gt=0)
    auth_required: bool | None = None


class NewsArticleRead(BaseModel):
    id: str
    source_id: str
    asset_id: str | None = None
    market_pair_id: str | None = None
    title: str
    summary: str | None = None
    url: str
    category: str | None = None
    sentiment_polarity: str | None = None
    sentiment_score: float | None = None
    impact_score: float | None = None
    reliability_score: float
    published_at: datetime | None = None
    collected_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NewsEventRead(BaseModel):
    id: str
    article_id: str
    asset_id: str | None = None
    market_pair_id: str | None = None
    event_type: str
    severity: int
    impact_score: float
    confidence: float
    detected_at: datetime
    explanation: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SentimentRecordRead(BaseModel):
    id: int
    source_id: str
    asset_id: str | None = None
    platform: str
    sentiment_score: float
    confidence_score: float
    subjectivity_score: float | None = None
    mention_weight: float
    collected_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SentimentSourceRead(BaseModel):
    id: str
    source_name: str
    platform: str
    enabled: bool
    rate_limit_per_minute: int
    reliability_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FearGreedSnapshotRead(BaseModel):
    id: int
    scope_type: str
    scope_id: str
    index_value: float
    index_label: str
    volatility_component: float | None = None
    trend_component: float | None = None
    volume_component: float | None = None
    sentiment_component: float | None = None
    news_component: float | None = None
    captured_at: datetime


class MarketRegimeSnapshotRead(BaseModel):
    id: int
    market_pair_id: str | None = None
    asset_id: str | None = None
    timeframe: str
    regime: str
    confidence: float
    trend_strength: float | None = None
    volatility_score: float | None = None
    liquidity_score: float | None = None
    detected_at: datetime


class IntelligenceSnapshotRead(BaseModel):
    id: str
    asset_id: str | None = None
    market_pair_id: str | None = None
    scope_type: str
    timeframe: str | None = None
    intelligence_score: float
    news_score: float | None = None
    social_sentiment_score: float | None = None
    market_sentiment_score: float | None = None
    fear_greed_index: float | None = None
    regime: str | None = None
    regime_confidence: float | None = None
    overall_confidence: float
    risk_modifier: float
    explanation: str | None = None
    generated_at: datetime


class IntelligenceAlertRead(BaseModel):
    id: str
    asset_id: str | None = None
    market_pair_id: str | None = None
    alert_type: str
    severity: str
    title: str
    message: str
    trigger_snapshot_id: str | None = None
    status: str
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}