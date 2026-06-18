from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.models.identity import User
from app.database.repositories.trading_repository import StrategyRepository
from app.database.session import SessionLocal
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.backtest_service import BacktestService
from app.services.exchange_service import ExchangeService
from app.services.feature_flag_service import FeatureFlagService
from app.services.health_service import HealthService
from app.services.market_service import MarketService
from app.services.notification_service import NotificationService
from app.services.paper_trading_service import PaperTradingService
from app.services.plugin_registry import PluginRegistry
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.strategy_config_manager import StrategyConfigManager
from app.services.strategy_engine import StrategyEngine
from app.services.token_blacklist import token_blacklist
from app.services.trade_journal_service import TradeJournalService
from app.services.trading_service import ExecutionService, SignalService, StrategyService
from app.services.user_service import UserService

_registry: PluginRegistry | None = None


def get_db() -> Generator[Session, None, None]:
    if callable(SessionLocal):
        db = SessionLocal()
        should_close = True
    else:
        db = SessionLocal
        should_close = False
    try:
        yield db
    finally:
        if should_close:
            db.close()


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def get_strategy_engine(registry: Annotated[PluginRegistry, Depends(get_plugin_registry)]) -> StrategyEngine:
    return StrategyEngine(registry)


def get_strategy_config_manager(
    db: Annotated[Session, Depends(get_db)],
    registry: Annotated[PluginRegistry, Depends(get_plugin_registry)],
) -> StrategyConfigManager:
    return StrategyConfigManager(StrategyRepository(db), registry)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    jti = payload.get("jti")
    if jti and token_blacklist.is_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = db.get(User, payload["sub"])
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)


def get_health_service() -> HealthService:
    return HealthService()


def get_exchange_service(db: Annotated[Session, Depends(get_db)]) -> ExchangeService:
    return ExchangeService(db)


def get_market_service(db: Annotated[Session, Depends(get_db)]) -> MarketService:
    return MarketService(db)


def get_risk_service(db: Annotated[Session, Depends(get_db)]) -> RiskService:
    return RiskService(db)


def get_strategy_service(db: Annotated[Session, Depends(get_db)]) -> StrategyService:
    return StrategyService(db)


def get_signal_service(db: Annotated[Session, Depends(get_db)]) -> SignalService:
    return SignalService(db)


def get_execution_service(db: Annotated[Session, Depends(get_db)]) -> ExecutionService:
    return ExecutionService(db, feature_flag_service=FeatureFlagService(db))


def get_feature_flag_service(db: Annotated[Session, Depends(get_db)]) -> FeatureFlagService:
    return FeatureFlagService(db)


def get_paper_trading_service(db: Annotated[Session, Depends(get_db)]) -> PaperTradingService:
    return PaperTradingService(db, feature_flag_service=FeatureFlagService(db))


def get_portfolio_service(db: Annotated[Session, Depends(get_db)]) -> PortfolioService:
    return PortfolioService(db)


def get_audit_service(db: Annotated[Session, Depends(get_db)]) -> AuditService:
    return AuditService(db)


def get_notification_service(db: Annotated[Session, Depends(get_db)]) -> NotificationService:
    return NotificationService(db)


def get_backtest_service(db: Annotated[Session, Depends(get_db)]) -> BacktestService:
    return BacktestService(db)


def get_safety_orchestrator(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.trading_safety import SafetyOrchestrator
    from app.services.trading_safety.kill_switch_service import KillSwitchService
    return SafetyOrchestrator(db, KillSwitchService(db))


def get_kill_switch_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.trading_safety.kill_switch_service import KillSwitchService
    return KillSwitchService(db)


def get_redis_client() -> Any:
    from app.integrations.redis.client import RedisClient
    return RedisClient()


def get_redis_client_optional() -> Any:
    try:
        from app.integrations.redis.client import RedisClient
        return RedisClient()
    except Exception:
        return None


def get_trade_journal_service(db: Annotated[Session, Depends(get_db)]) -> TradeJournalService:
    return TradeJournalService(db)
