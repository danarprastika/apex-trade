from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str | None = None


class TagResponse(BaseModel):
    id: str
    name: str
    color: str
    usage_count: int
    created_at: str

    model_config = {"from_attributes": True}


class TradeScreenshotResponse(BaseModel):
    id: str
    url: str
    caption: str | None
    stage: str | None
    sort_order: int
    created_at: str

    model_config = {"from_attributes": True}


class TradeJournalCreate(BaseModel):
    trade_id: str
    entry_reason: str = Field(min_length=1, max_length=10000)
    exit_reason: str = Field(min_length=1, max_length=10000)
    notes: str | None = None
    lessons_learned: str | None = None
    risk_score: int | None = Field(default=None, ge=1, le=10)
    tag_names: list[str] = Field(default_factory=list)
    screenshot_urls: list[str] = Field(default_factory=list)


class TradeJournalUpdate(BaseModel):
    entry_reason: str | None = None
    exit_reason: str | None = None
    notes: str | None = None
    lessons_learned: str | None = None
    risk_score: int | None = Field(default=None, ge=1, le=10)
    add_tags: list[str] = Field(default_factory=list)
    remove_tags: list[str] = Field(default_factory=list)
    remove_screenshot_ids: list[str] = Field(default_factory=list)


class TradeJournalResponse(BaseModel):
    id: str
    trade_id: str
    signal_id: str | None
    strategy_id: str
    strategy_name: str
    entry_reason: str
    exit_reason: str
    notes: str | None
    lessons_learned: str | None
    risk_score: int | None
    outcome: str | None
    tags: list[TagResponse] = Field(default_factory=list)
    screenshots: list[TradeScreenshotResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class JournalFilterParams(BaseModel):
    strategy_ids: list[str] | None = None
    outcome: list[str] | None = None
    risk_score_range: tuple[int, int] | None = None
    tags: list[str] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str) -> str:
        allowed = {"created_at", "updated_at", "risk_score", "outcome"}
        if value not in allowed:
            raise ValueError(f"sort_by must be one of {allowed}")
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: str) -> str:
        if value not in {"asc", "desc"}:
            raise ValueError("sort_order must be asc or desc")
        return value

    @field_validator("risk_score_range")
    @classmethod
    def validate_risk_range(cls, value: tuple[int, int] | None) -> tuple[int, int] | None:
        if value is None:
            return value
        if not (1 <= value[0] <= 10 and 1 <= value[1] <= 10):
            raise ValueError("risk_score_range must be between 1 and 10")
        if value[0] > value[1]:
            raise ValueError("risk_score_range min cannot be greater than max")
        return value


class JournalListResponse(BaseModel):
    items: list[TradeJournalResponse]
    total: int
    page: int
    size: int
    pages: int

    model_config = {"from_attributes": True}


class JournalStatistics(BaseModel):
    total_trades: int
    win_rate: float | None = None
    avg_risk_score: float | None = None
    avg_profit: float | None = None
    by_outcome: dict[str, int] | None = None
    by_strategy: dict[str, int] | None = None
    by_risk_score: dict[str, int] | None = None
    by_tag: dict[str, int] | None = None

    model_config = {"from_attributes": True}


class JournalPerformanceBreakdown(BaseModel):
    overall: JournalStatistics
    by_strategy: dict[str, JournalStatistics]
    by_tag: dict[str, JournalStatistics]
    by_risk_bucket: dict[str, JournalStatistics]

    model_config = {"from_attributes": True}


class JournalRiskCorrelation(BaseModel):
    correlation: float | None
    points: list[dict[str, Any]]

    model_config = {"from_attributes": True}


class JournalTimePatterns(BaseModel):
    by_hour: list[dict[str, Any]]
    by_day_of_week: list[dict[str, Any]]

    model_config = {"from_attributes": True}


class JournalTagEfficacy(BaseModel):
    items: list[dict[str, Any]]

    model_config = {"from_attributes": True}


class JournalAnalyticsSummary(BaseModel):
    performance_breakdown: JournalPerformanceBreakdown
    risk_correlation: JournalRiskCorrelation
    time_patterns: JournalTimePatterns
    tag_efficacy: JournalTagEfficacy

    model_config = {"from_attributes": True}
