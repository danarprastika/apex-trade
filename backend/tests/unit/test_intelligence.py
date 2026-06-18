from __future__ import annotations

import pytest

from app.database.models.intelligence import IntelligenceSource
from app.services.news_service import NewsService
from app.services.sentiment_service import (
    FearGreedService,
    RegimeDetectionService,
    SentimentService,
)


class TestIntelligenceModels:
    def test_intelligence_source_creation(self) -> None:
        source = IntelligenceSource(
            source_name="test-news",
            source_type="RSS",
            category="crypto",
            url="https://example.com/rss",
            enabled=True,
            reliability_score=75.0,
        )
        assert source.source_name == "test-news"
        assert source.enabled is True


class TestNewsService:
    @pytest.fixture
    def mock_news_service(self) -> NewsService:
        return NewsService(None)

    def test_compute_dedupe_hash(self) -> None:
        url = "https://example.com/article"
        title = "Test Article"
        hash1 = NewsService._compute_dedupe_hash(url, title)
        hash2 = NewsService._compute_dedupe_hash(url, title)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_compute_dedupe_hash_different(self) -> None:
        hash1 = NewsService._compute_dedupe_hash("https://a.com", "Title A")
        hash2 = NewsService._compute_dedupe_hash("https://b.com", "Title B")
        assert hash1 != hash2


class TestSentimentService:
    def test_compute_text_hash(self) -> None:
        text = "Bitcoin is going to the moon!"
        hash1 = SentimentService._compute_text_hash(text)
        hash2 = SentimentService._compute_text_hash(text)
        assert hash1 == hash2
        assert len(hash1) == 64


class TestFearGreedService:
    def test_get_label_extreme_fear(self) -> None:
        assert FearGreedService._get_label(10) == "Extreme Fear"

    def test_get_label_fear(self) -> None:
        assert FearGreedService._get_label(30) == "Fear"

    def test_get_label_neutral(self) -> None:
        assert FearGreedService._get_label(50) == "Neutral"

    def test_get_label_greed(self) -> None:
        assert FearGreedService._get_label(70) == "Greed"

    def test_get_label_extreme_greed(self) -> None:
        assert FearGreedService._get_label(90) == "Extreme Greed"


class TestRegimeDetectionService:
    def test_classify_regime_trending(self) -> None:
        service = RegimeDetectionService(None)
        regime = service._classify_regime(trend_strength=60, volatility_score=30, liquidity_score=70)
        assert regime == "TRENDING"

    def test_classify_regime_volatile(self) -> None:
        service = RegimeDetectionService(None)
        regime = service._classify_regime(trend_strength=20, volatility_score=70, liquidity_score=70)
        assert regime == "VOLATILE"

    def test_classify_regime_sideways(self) -> None:
        service = RegimeDetectionService(None)
        regime = service._classify_regime(trend_strength=20, volatility_score=30, liquidity_score=70)
        assert regime == "SIDEWAYS"

    def test_classify_regime_crisis(self) -> None:
        service = RegimeDetectionService(None)
        regime = service._classify_regime(trend_strength=-50, volatility_score=80, liquidity_score=20)
        assert regime == "CRISIS"
