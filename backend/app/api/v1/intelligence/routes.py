from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.intelligence.articles_routes import router as articles_router
from app.api.v1.intelligence.intel_routes import router as intel_router
from app.api.v1.intelligence.news_routes import router as news_router
from app.api.v1.intelligence.regime_routes import router as regime_router
from app.api.v1.intelligence.sentiment_routes import router as sentiment_router

api_router = APIRouter()

api_router.include_router(news_router, prefix="/news")
api_router.include_router(articles_router, prefix="/news")
api_router.include_router(sentiment_router, prefix="/sentiment")
api_router.include_router(regime_router, prefix="/market-regimes")
api_router.include_router(intel_router, prefix="/intelligence")