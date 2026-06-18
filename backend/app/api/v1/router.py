from fastapi import APIRouter

from app.api.v1.admin import routes as admin
from app.api.v1.auth import routes as auth
from app.api.v1.backtest import routes as backtest
from app.api.v1.exchanges import routes as exchanges
from app.api.v1.feature_flags import routes as feature_flags
from app.api.v1.health import routes as health
from app.api.v1.intelligence import routes as intelligence
from app.api.v1.journal import router as journal
from app.api.v1.market import routes as market
from app.api.v1.notifications import routes as notifications
from app.api.v1.portfolio import routes as portfolio
from app.api.v1.risk import routes as risk
from app.api.v1.safety import routes as safety
from app.api.v1.trading import routes as trading
from app.api.v1.users import routes as users

api_router = APIRouter()

api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(feature_flags.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(exchanges.router, prefix="/exchanges", tags=["exchanges"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(journal, prefix="/journal", tags=["journal"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(intelligence.api_router, prefix="/intelligence", tags=["intelligence"])
