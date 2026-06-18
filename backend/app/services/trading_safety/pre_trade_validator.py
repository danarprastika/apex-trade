from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.database.repositories.exchange_repository import ExchangeAccountRepository, ExchangeRepository
from app.database.repositories.portfolio_repository import PortfolioRepository
from app.database.repositories.risk_repository import RiskProfileRepository, RiskEventRepository
from app.database.repositories.trading_repository import OrderRepository, StrategyRepository
from app.database.repositories.trading_safety_repository import ExposureLimitRepository
from app.domain.safety.value_objects import SafetyContext, SafetyDecision, ValidationLayer
from app.integrations.exchanges.failover.manager import ExchangeFailoverManager
from app.integrations.exchanges.registry import ExchangeAdapterRegistry
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)


class PreTradeValidator:
    def __init__(
        self,
        db: Session,
        kill_switch_service: Any,
        market_data_quality_service: Any | None = None,
        event_bus: Any | None = None,
    ):
        self.db = db
        self.kill_switch = kill_switch_service
        self.market_data_quality = market_data_quality_service
        self.event_bus = event_bus
        self.orders = OrderRepository(db)
        self.accounts = ExchangeAccountRepository(db)
        self.exchanges = ExchangeRepository(db)
        self.strategies = StrategyRepository(db)
        self.risk_service = RiskService(db)
        self.exposure_limits = ExposureLimitRepository(db)
        self.portfolios = PortfolioRepository(db)
        self.risk_events = RiskEventRepository(db)

    def validate(self, context: SafetyContext) -> SafetyDecision:
        decision = SafetyDecision(approved=True, reasons=[], checks_performed={}, execution_blocked_by=[])

        if self.kill_switch.is_global_kill_enabled():
            decision.add_rejection(ValidationLayer.KILL_SWITCH, "Global kill switch is active")

        if self.kill_switch.is_user_kill_enabled(context.user_id):
            decision.add_rejection(ValidationLayer.KILL_SWITCH, f"User kill switch active for {context.user_id}")

        account = self.accounts.get(context.exchange_account_id)
        if not account:
            decision.add_rejection(ValidationLayer.KILL_SWITCH, "Exchange account not found")
        elif self.kill_switch.is_exchange_kill_enabled(str(account.exchange_id)):
            decision.add_rejection(ValidationLayer.KILL_SWITCH, f"Exchange kill switch active")

        if context.strategy_id and self.kill_switch.is_strategy_kill_enabled(context.strategy_id):
            decision.add_rejection(ValidationLayer.KILL_SWITCH, f"Strategy kill switch active")

        if context.quantity is not None and context.quantity <= 0:
            decision.add_rejection(ValidationLayer.ORDER_SIZE_LIMIT, "Quantity must be greater than zero")

        profile = self._get_risk_profile(context.user_id)
        if profile and context.quantity:
            portfolio = self.portfolios.get_by_user(context.user_id)
            if portfolio and portfolio.total_value > 0:
                position_risk_pct = (context.quantity / float(portfolio.total_value)) * 100
                if position_risk_pct > float(profile.max_risk_per_trade):
                    decision.add_rejection(
                        ValidationLayer.DAILY_LOSS_LIMIT,
                        f"Position size exceeds {profile.max_risk_per_trade}% of portfolio",
                    )

            if self._daily_loss_exceeded(profile, context.user_id):
                decision.add_rejection(ValidationLayer.DAILY_LOSS_LIMIT, "Daily loss limit reached")

        if context.symbol and context.user_id:
            self._check_exposure_limits(context, decision)

        if context.strategy_id:
            strategy = self.strategies.get(context.strategy_id)
            if not strategy:
                decision.add_rejection(ValidationLayer.KILL_SWITCH, "Strategy not found")

        self._log_validation_result(context, decision)

        return decision

    def _get_risk_profile(self, user_id: str) -> Any:
        try:
            return self.risk_service.get_profile(user_id)
        except Exception:
            return None

    def _daily_loss_exceeded(self, profile: Any, user_id: str) -> bool:
        from datetime import datetime, timezone
        from sqlalchemy import func, select
        from app.database.models.trading import Trade, Position
        from app.database.models.exchange import ExchangeAccount

        today = datetime.now(timezone.utc).date()
        result = self.db.scalar(
            select(func.coalesce(func.sum(Trade.net_profit), 0))
            .select_from(Trade)
            .join(Position, Trade.position_id == Position.id)
            .join(ExchangeAccount, Position.exchange_account_id == ExchangeAccount.id)
            .where(
                (Trade.net_profit < 0)
                & (func.date(Trade.closed_at) == today)
                & (ExchangeAccount.user_id == user_id)
            )
        )
        daily_loss = abs(float(result or 0))
        return daily_loss >= float(profile.max_daily_loss)

    def _check_exposure_limits(self, context: SafetyContext, decision: SafetyDecision) -> None:
        if not context.symbol:
            return

        limits = self.exposure_limits.get_all_for_user(context.user_id, limit=10)
        for limit in limits:
            if limit.current_exposure_percentage >= limit.max_exposure_percentage:
                decision.add_rejection(
                    ValidationLayer.EXPOSURE_LIMIT,
                    f"Exposure limit exceeded: {limit.asset_id or limit.exchange_id}",
                )

    def _log_validation_result(self, context: SafetyContext, decision: SafetyDecision) -> None:
        if not decision.approved:
            self.risk_events.create(
                user_id=context.user_id,
                event_type="PRETRADE_REJECTED",
                severity="HIGH",
                description="; ".join(decision.reasons),
            )