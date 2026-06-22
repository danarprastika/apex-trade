"""API v1 router."""

from fastapi import APIRouter

router = APIRouter()

# Health check endpoints (skip auth for monitoring)
@router.get("/health")
async def api_health() -> dict:
    return {"status": "ok"}

# Placeholder for future v1 endpoints
# from src.presentation.api.v1.trading.router import router as trading_router
# router.include_router(trading_router, prefix="/trading", tags=["trading"])
