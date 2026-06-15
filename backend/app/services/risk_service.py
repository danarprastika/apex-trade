from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.database.models.exchange import ExchangeAccount
from app.database.models.portfolio import Portfolio
from app.database.models.risk import RiskEvent, RiskProfile
from app.database.models.trading import Position, Trade
from app.database.repositories.portfolio_repository import PortfolioRepository
from app.database.repositories.risk_repository import RiskEventRepository, RiskProfileRepository
from app.database.repositories.trading_repository import PositionRepository, TradeRepository
from app.schemas.risk import RiskDecision

logger = logging.getLogger(__name__)


class RiskService:
    def __init__(self, db: Session):
        self.db = db
        self.profiles = RiskProfileRepository(db)
        self.events = RiskEventRepository(db)
        self.portfolios = PortfolioRepository(db)
        self.positions = PositionRepository(db)
        self.trades = TradeRepository(db)

    def create_profile(
        self,
        user_id: str,
        max_risk_per_trade: float,
        max_daily_loss: float,
        max_drawdown: float,
        max_open_positions: int,
    ) -> RiskProfile:
        existing_profile = self.profiles.get_by_user(user_id)
        if existing_profile:
            raise ValidationError("Risk profile already exists for user")

        profile = self.profiles.create(
            user_id=user_id,
            max_risk_per_trade=max_risk_per_trade,
            max_daily_loss=max_daily_loss,
            max_drawdown=max_drawdown,
            max_open_positions=max_open_positions,
        )
        self.profiles.commit()
        self.profiles.refresh(profile)
        logger.info("Created risk profile profile_id=%s user_id=%s", profile.id, user_id)
        return profile

    def get_profile(self, user_id: str) -> RiskProfile:
        profile = self.profiles.get_by_user(user_id)
        if not profile:
            raise NotFoundError("Risk profile not found")
        return profile

    def evaluate(self, user_id: str, risk_score: float, requested_position_size: float | None = None) -> RiskDecision:
        profile = self.get_profile(user_id)
        portfolio = self.portfolios.get_by_user(user_id)
        open_positions = self._count_open_positions(user_id)
        daily_loss = abs(self._today_realized_loss(user_id))
        drawdown = self._drawdown(portfolio)
        position_risk_percentage = self._position_risk_percentage(requested_position_size, portfolio)
        veto_reasons: list[str] = []

        if risk_score < 0 or risk_score > 100:
            veto_reasons.append("risk score must be between 0 and 100")
        if risk_score > profile.max_risk_per_trade:
            veto_reasons.append("risk score exceeds max_risk_per_trade")
        if risk_score > 85:
            veto_reasons.append("risk score exceeds hard ceiling 85")
        if requested_position_size is not None and requested_position_size <= 0:
            veto_reasons.append("requested position size must be greater than zero")
        if requested_position_size is not None and portfolio and portfolio.total_value > 0 and position_risk_percentage > profile.max_risk_per_trade:
            veto_reasons.append("requested notional exceeds max_risk_per_trade percentage of portfolio")
        if requested_position_size is not None and (not portfolio or portfolio.total_value <= 0):
            veto_reasons.append("portfolio value is required for notional risk validation")
        if open_positions >= profile.max_open_positions:
            veto_reasons.append("max open positions reached")
        if daily_loss >= profile.max_daily_loss:
            veto_reasons.append("daily loss limit reached")
        if drawdown >= profile.max_drawdown:
            veto_reasons.append("drawdown limit reached")

        allowed = not veto_reasons
        if not allowed:
            logger.warning("Risk veto user_id=%s reasons=%s", user_id, veto_reasons)
            self.log_event(user_id, "RISK_VETO", "HIGH", "; ".join(veto_reasons))

        return RiskDecision(
            allowed=allowed,
            reason="approved" if allowed else "risk limit exceeded",
            risk_score=risk_score,
            position_size=requested_position_size,
            max_risk_per_trade=float(profile.max_risk_per_trade),
            max_daily_loss=float(profile.max_daily_loss),
            max_drawdown=float(profile.max_drawdown),
            max_open_positions=int(profile.max_open_positions),
            open_positions=open_positions,
            daily_loss=daily_loss,
            drawdown=drawdown,
            veto_reasons=veto_reasons,
        )

    def log_event(self, user_id: str, event_type: str, severity: str, description: str) -> RiskEvent:
        event = self.events.create(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            description=description,
        )
        self.events.commit()
        self.events.refresh(event)
        return event

    def list_events(self, user_id: str, limit: int = 100) -> list[RiskEvent]:
        return self.events.list_by_user(user_id, limit=limit)

    def _count_open_positions(self, user_id: str) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Position)
                .join(ExchangeAccount, Position.exchange_account_id == ExchangeAccount.id)
                .where((ExchangeAccount.user_id == user_id) & (Position.status == "OPEN"))
            )
            or 0
        )

    def _today_realized_loss(self, user_id: str) -> float:
        today = datetime.now(timezone.utc).date()
        result = self.db.scalar(
            select(func.coalesce(func.sum(Trade.net_profit), 0))
            .select_from(Trade)
            .join(Position, Trade.position_id == Position.id)
            .join(ExchangeAccount, Position.exchange_account_id == ExchangeAccount.id)
            .where(
                (ExchangeAccount.user_id == user_id)
                & (Trade.net_profit < 0)
                & (func.date(Trade.closed_at) == today)
            )
        )
        return float(result or 0)

    @staticmethod
    def _drawdown(portfolio: Portfolio | None) -> float:
        if not portfolio:
            return 0.0
        return max(0.0, float(portfolio.risk_score))

    @staticmethod
    def _position_risk_percentage(requested_position_size: float | None, portfolio: Portfolio | None) -> float | None:
        if requested_position_size is None or not portfolio or portfolio.total_value <= 0:
            return None
        return (float(requested_position_size) / float(portfolio.total_value)) * 100
