"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.presentation.api.dependencies import setup_dependencies
from app.presentation.api.v1 import trading, portfolio, market_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="QuantX AI API",
    description="AI-powered personal trading platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(market_data.router, prefix="/api/v1/market-data", tags=["market-data"])


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    return {"status": "ok"}


setup_dependencies(app)
