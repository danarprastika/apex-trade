from __future__ import annotations

import logging

from datetime import datetime

from app.database.session import SessionLocal
from app.services.news_service import NewsService
from app.services.sentiment_service import SentimentService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.collectors.fetch_news_articles")
def fetch_news_articles(source_id: str | None = None, limit: int = 50) -> dict[str, object]:
    db = SessionLocal()
    event_bus = None
    try:
        news_service = NewsService(db)
        persisted = 0
        duplicates = 0

        articles = _fetch_synthetic_articles(limit)
        for article in articles:
            result = news_service.collect_article(
                source_name=article["source_name"],
                title=article["title"],
                url=article["url"],
                published_at=article.get("published_at"),
                raw_payload=article.get("raw_payload"),
            )
            if result:
                persisted += 1
            else:
                duplicates += 1

        logger.info("Fetched news articles persisted=%s duplicates=%s", persisted, duplicates)

        if event_bus:
            for article in articles:
                event = ApexEvent(
                    type="NEWS.COLLECTED",
                    payload={"url": article["url"], "title": article["title"]},
                    source="news-collector",
                )
                event_bus.publish(event)

        return {
            "source_id": source_id,
            "limit": limit,
            "fetched": len(articles),
            "persisted": persisted,
            "duplicates": duplicates,
            "status": "ok",
        }
    except Exception as exc:
        logger.exception("News collection failed")
        return {
            "source_id": source_id,
            "limit": limit,
            "status": "error",
            "error": str(exc),
        }
    finally:
        db.close()


@celery_app.task(name="tasks.collectors.fetch_sentiment")
def fetch_sentiment(platform: str | None = None, limit: int = 100) -> dict[str, object]:
    db = SessionLocal()
    try:
        from app.services.sentiment_service import SentimentService

        sentiment_service = SentimentService(db)
        persisted = 0

        records = _fetch_synthetic_sentiment(limit)
        for record in records:
            result = sentiment_service.collect_sentiment(
                platform=record["platform"],
                text=record["text"],
                asset_symbols=record.get("asset_symbols"),
            )
            if result:
                persisted += 1

        logger.info("Fetched sentiment records persisted=%s", persisted)

        return {
            "platform": platform,
            "limit": limit,
            "fetched": len(records),
            "persisted": persisted,
            "status": "ok",
        }
    except Exception as exc:
        logger.exception("Sentiment collection failed")
        return {
            "platform": platform,
            "limit": limit,
            "status": "error",
            "error": str(exc),
        }
    finally:
        db.close()


def _fetch_synthetic_articles(limit: int) -> list[dict]:
    articles = []
    for i in range(min(limit, 10)):
        articles.append({
            "source_name": "test-news",
            "title": f"Test News Article {i+1}",
            "url": f"https://example.com/news/{i+1}",
            "published_at": datetime.utcnow(),
            "raw_payload": {"synthetic": True, "index": i+1},
        })
    return articles


def _fetch_synthetic_sentiment(limit: int) -> list[dict]:
    records = []
    for i in range(min(limit, 10)):
        records.append({
            "platform": "twitter",
            "text": f"Test sentiment post about BTC {i+1}",
            "asset_symbols": ["BTC"],
        })
    return records