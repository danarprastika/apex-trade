from __future__ import annotations

import hashlib
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.intelligence import NewsArticle, NewsEvent
from app.database.repositories.intelligence_repository import (
    NewsArticleRepository,
    NewsEventRepository,
    IntelligenceSourceRepository,
)
from app.services.market_service import MarketService

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, db: Session):
        self.db = db
        self.sources = IntelligenceSourceRepository(db)
        self.articles = NewsArticleRepository(db)
        self.events = NewsEventRepository(db)
        self.market_service = MarketService(db)

    def collect_article(
        self,
        source_name: str,
        title: str,
        url: str,
        published_at: datetime | None = None,
        raw_payload: dict | None = None,
    ) -> NewsArticle | None:
        source = self.sources.get_by_name(source_name)
        if not source:
            logger.warning("Unknown news source: %s", source_name)
            return None

        dedupe_hash = self._compute_dedupe_hash(url, title)
        existing = self.articles.get_by_dedupe_hash(dedupe_hash)
        if existing:
            logger.info("Duplicate article ignored source=%s url=%s", source_name, url)
            return existing

        article = self.articles.create(
            source_id=source.id,
            asset_id=None,
            market_pair_id=None,
            title=title,
            summary=None,
            url=url,
            published_at=published_at,
            dedupe_hash=dedupe_hash,
            raw_payload=raw_payload,
            reliability_score=source.reliability_score,
        )
        self.articles.commit()
        self.articles.refresh(article)
        return article

    def classify_article(
        self,
        article_id: str,
        category: str | None = None,
        sentiment_polarity: str | None = None,
        sentiment_score: float | None = None,
        impact_score: float | None = None,
    ) -> NewsArticle | None:
        article = self.articles.get(article_id)
        if not article:
            return None

        self.articles.update(
            article,
            category=category,
            sentiment_polarity=sentiment_polarity,
            sentiment_score=sentiment_score,
            impact_score=impact_score,
        )
        self.articles.commit()
        return article

    def resolve_asset_for_article(
        self,
        article_id: str,
        asset_symbols: list[str] | None = None,
    ) -> NewsArticle | None:
        article = self.articles.get(article_id)
        if not article:
            return None

        if asset_symbols:
            for symbol in asset_symbols:
                asset = self.market_service.get_or_create_asset(symbol, "CRYPTO")
                self.articles.update(article, asset_id=asset.id)
                self.articles.commit()

        return article

    def detect_event(
        self,
        article_id: str,
        event_type: str,
        severity: int,
        impact_score: float,
        confidence: float = 0.0,
        explanation: str | None = None,
    ) -> NewsEvent | None:
        article = self.articles.get(article_id)
        if not article:
            return None

        event = self.events.create(
            article_id=article_id,
            asset_id=article.asset_id,
            market_pair_id=article.market_pair_id,
            event_type=event_type,
            severity=severity,
            impact_score=impact_score,
            confidence=confidence,
            explanation=explanation,
        )
        self.events.commit()
        self.events.refresh(event)
        return event

    def list_articles(
        self,
        asset_id: str | None = None,
        market_pair_id: str | None = None,
        category: str | None = None,
        min_impact_score: float | None = None,
        limit: int = 100,
    ) -> list[NewsArticle]:
        query = select(NewsArticle)
        if asset_id:
            query = query.where(NewsArticle.asset_id == asset_id)
        if market_pair_id:
            query = query.where(NewsArticle.market_pair_id == market_pair_id)
        if category:
            query = query.where(NewsArticle.category == category)
        if min_impact_score is not None:
            query = query.where(NewsArticle.impact_score >= min_impact_score)
        return self.db.scalars(query.order_by(NewsArticle.published_at.desc()).limit(limit)).all()

    def list_events(
        self,
        event_type: str | None = None,
        asset_id: str | None = None,
        limit: int = 100,
    ) -> list[NewsEvent]:
        query = select(NewsEvent)
        if event_type:
            query = query.where(NewsEvent.event_type == event_type)
        if asset_id:
            query = query.where(NewsEvent.asset_id == asset_id)
        return self.db.scalars(query.order_by(NewsEvent.detected_at.desc()).limit(limit)).all()

    @staticmethod
    def _compute_dedupe_hash(url: str, title: str) -> str:
        content = f"{url}:{title}"
        return hashlib.sha256(content.encode()).hexdigest()[:64]