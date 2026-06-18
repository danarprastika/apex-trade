from fastapi import APIRouter

from app.api.v1.journal.routes.health import router as health_router
from app.api.v1.journal.routes.trades import router as trades_router

router = APIRouter()
router.include_router(health_router)
router.include_router(trades_router)

__all__ = ["router"]
