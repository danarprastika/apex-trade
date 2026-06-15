from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.models.identity import User
from app.database.session import SessionLocal
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.exchange_service import ExchangeService
from app.services.health_service import HealthService
from app.services.market_service import MarketService
from app.services.notification_service import NotificationService
from app.services.paper_trading_service import PaperTradingService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.trading_service import ExecutionService, SignalService, StrategyService
from app.services.user_service import UserService


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Annotated[str | None, Header()],
    db: Annotated[Session, Depends(get_db)],
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
    return ExecutionService(db)


def get_paper_trading_service(db: Annotated[Session, Depends(get_db)]) -> PaperTradingService:
    return PaperTradingService(db)


def get_portfolio_service(db: Annotated[Session, Depends(get_db)]) -> PortfolioService:
    return PortfolioService(db)


def get_audit_service(db: Annotated[Session, Depends(get_db)]) -> AuditService:
    return AuditService(db)


def get_notification_service(db: Annotated[Session, Depends(get_db)]) -> NotificationService:
    return NotificationService(db)
