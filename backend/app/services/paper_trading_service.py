from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.encryption import encrypt_secret
from app.core.config import settings
from app.core.exceptions import FeatureDisabledError, NotFoundError, ValidationError
from app.database.models.audit import AuditLog
from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.models.notification import Notification
from app.database.models.portfolio import Portfolio, PortfolioSnapshot
from app.database.models.risk import RiskEvent, RiskProfile
from app.database.models.trading import Order, Position, Trade
from app.database.repositories.exchange_repository import ExchangeAccountRepository, ExchangeRepository
from app.database.repositories.market_repository import MarketPairRepository
from app.database.repositories.notification_repository import NotificationRepository
from app.database.repositories.portfolio_repository import PortfolioRepository, PortfolioSnapshotRepository
from app.database.repositories.risk_repository import RiskEventRepository, RiskProfileRepository
from app.database.repositories.trading_repository import OrderRepository, PositionRepository, StrategyRepository, TradeRepository
from app.services.feature_flag_service import FeatureFlagService
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)


class PaperTradingResult:
    def __init__(self, order: Order, position: Position | None, trade: Trade | None, risk_allowed: bool, risk_reason: str, message: str):
        self.order = order
        self.position = position
        self.trade = trade
        self.risk_allowed = risk_allowed
        self.risk_reason = risk_reason
        self.message = message

    def to_dict(self) -> dict[str, object]:
        return {
            "order": self.order,
            "position": self.position,
            "trade": self.trade,
            "risk_allowed": self.risk_allowed,
            "risk_reason": self.risk_reason,
            "message": self.message,
        }


class PaperTradingService:
    def __init__(self, db: Session, feature_flag_service: FeatureFlagService | None = None):
        self.db = db
        self.feature_flags = feature_flag_service or FeatureFlagService(db)
        self.exchanges = ExchangeRepository(db)
        self.accounts = ExchangeAccountRepository(db)
        self.market_pairs = MarketPairRepository(db)
        self.orders = OrderRepository(db)
        self.portfolios = PortfolioRepository(db)
        self.portfolio_snapshots = PortfolioSnapshotRepository(db)
        self.positions = PositionRepository(db)
        self.risk_events = RiskEventRepository(db)
        self.risk_profiles = RiskProfileRepository(db)
        self.strategies = StrategyRepository(db)
        self.trades = TradeRepository(db)
        self.notifications = NotificationRepository(db)
        self.risk_service = RiskService(db)

    def execute_order(
        self,
        user_id: str,
        market_pair_id: str,
        strategy_id: str,
        side: str,
        quantity: float,
        price: float | None,
        signal_id: str | None = None,
    ) -> PaperTradingResult:
        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValidationError("Paper order side must be BUY or SELL")
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if price is None or price <= 0:
            raise ValidationError("Paper order price is required")

        self._require_paper_trading_enabled(user_id)

        market_pair = self.market_pairs.get(market_pair_id)
        if not market_pair:
            raise NotFoundError("Market pair not found")
        if not self.strategies.get(strategy_id):
            raise NotFoundError("Strategy not found")

        portfolio = self._get_or_create_portfolio(user_id)
        self._get_or_create_risk_profile(user_id)
        exchange = self._get_or_create_paper_exchange()
        account = self._get_or_create_paper_account(user_id, exchange.id)
        risk_score = self._calculate_risk_score(quantity, price, portfolio)
        risk_decision = self.risk_service.evaluate(user_id, risk_score, quantity * price)
        risk_allowed = risk_decision.allowed

        order = self.orders.create(
            exchange_account_id=account.id,
            signal_id=signal_id,
            exchange_order_id=None,
            order_type="MARKET",
            side=normalized_side,
            quantity=quantity,
            price=price,
            filled_quantity=0,
            status="NEW",
        )

        if not risk_allowed:
            order.status = "REJECTED"
            self.orders.commit()
            self.orders.refresh(order)
            self._log_risk_event(user_id, "PAPER_ORDER_REJECTED", "HIGH", "Paper order rejected by risk engine")
            self._notify(user_id, "RISK", "Paper order rejected", "Risk engine rejected your paper order.")
            return PaperTradingResult(order, None, None, False, "; ".join(risk_decision.veto_reasons), "Paper order rejected by risk engine")

        try:
            if normalized_side == "BUY":
                position = self._execute_buy(portfolio, account.id, market_pair_id, strategy_id, quantity, price, signal_id)
                trade = None
            else:
                position, trade = self._execute_sell(portfolio, account.id, market_pair_id, strategy_id, quantity, price, signal_id)

            order.status = "FILLED"
            order.filled_quantity = quantity
            order.exchange_order_id = f"PAPER-{order.id}"
            self.orders.update(order)
            self._snapshot(portfolio)
            self.db.commit()
            self.db.refresh(order)
            if position:
                self.db.refresh(position)
            if trade:
                self.db.refresh(trade)
            self._log_audit(user_id, "ORDER", order.id, "PAPER_ORDER_EXECUTED", {"side": normalized_side, "quantity": quantity, "price": price})
            self._notify(user_id, "TRADE", "Paper order filled", f"Paper {normalized_side} order filled for {quantity} at {price}.")
            logger.info("Paper order executed order_id=%s user_id=%s", order.id, user_id)
            return PaperTradingResult(order, position, trade, True, "approved", "Paper order executed")
        except ValidationError as exc:
            order.status = "REJECTED"
            self.orders.update(order)
            self.db.commit()
            self.db.refresh(order)
            self._log_risk_event(user_id, "PAPER_ORDER_REJECTED", "MEDIUM", str(exc))
            self._notify(user_id, "RISK", "Paper order rejected", str(exc))
            return PaperTradingResult(order, None, None, False, str(exc), str(exc))

    def _get_or_create_portfolio(self, user_id: str) -> Portfolio:
        portfolio = self.portfolios.get_by_user(user_id)
        if portfolio:
            return portfolio
        portfolio = Portfolio(user_id=user_id, portfolio_name="Default", currency="USDT", total_value=0, cash_balance=0, risk_score=0)
        self.portfolios.add(portfolio)
        self.db.flush()
        return portfolio

    def _get_or_create_risk_profile(self, user_id: str) -> RiskProfile:
        profile = self.risk_profiles.get_by_user(user_id)
        if profile:
            return profile
        profile = RiskProfile(
            user_id=user_id,
            max_risk_per_trade=1.0,
            max_daily_loss=3.0,
            max_drawdown=15.0,
            max_open_positions=5,
        )
        self.risk_profiles.add(profile)
        self.db.flush()
        return profile

    def _get_or_create_paper_exchange(self) -> Exchange:
        exchange = self.exchanges.get_by_name_and_type("Paper Trading", "PAPER")
        if exchange:
            return exchange
        exchange = self.exchanges.create(name="Paper Trading", exchange_type="PAPER", status="ACTIVE")
        self.exchanges.commit()
        self.exchanges.refresh(exchange)
        return exchange

    def _get_or_create_paper_account(self, user_id: str, exchange_id: str) -> ExchangeAccount:
        account = self.accounts.get_by_user_and_exchange(user_id, exchange_id)
        if account:
            return account
        account = self.accounts.create(
            user_id=user_id,
            exchange_id=exchange_id,
            api_key_encrypted=encrypt_secret("paper-api-key"),
            api_secret_encrypted=encrypt_secret("paper-api-secret"),
            is_testnet=True,
            status="ACTIVE",
        )
        self.accounts.commit()
        self.accounts.refresh(account)
        return account

    def _calculate_risk_score(self, quantity: float, price: float, portfolio: Portfolio) -> float:
        notional = quantity * price
        if portfolio.total_value <= 0:
            return 50.0
        return min(100.0, (notional / portfolio.total_value) * 100)

    def _execute_buy(
        self,
        portfolio: Portfolio,
        account_id: str,
        market_pair_id: str,
        strategy_id: str,
        quantity: float,
        price: float,
        signal_id: str | None,
    ) -> Position:
        notional = quantity * price
        if portfolio.cash_balance < notional:
            raise ValidationError("Insufficient paper cash balance")

        existing_position = self.positions.get_open(account_id, market_pair_id, strategy_id)
        now = datetime.now(timezone.utc)
        portfolio.cash_balance -= notional
        if existing_position:
            total_quantity = existing_position.quantity + quantity
            existing_position.entry_price = ((existing_position.entry_price * existing_position.quantity) + (price * quantity)) / total_quantity
            existing_position.quantity = total_quantity
            existing_position.current_price = price
            existing_position.unrealized_pnl = (price - existing_position.entry_price) * existing_position.quantity
            existing_position.updated_at = now
            portfolio.total_value = portfolio.cash_balance + (existing_position.quantity * existing_position.current_price)
            return existing_position

        position = Position(
            exchange_account_id=account_id,
            market_pair_id=market_pair_id,
            strategy_id=strategy_id,
            entry_order_id=None,
            entry_price=price,
            quantity=quantity,
            current_price=price,
            unrealized_pnl=0,
            status="OPEN",
            opened_at=now,
            closed_at=None,
        )
        self.positions.add(position)
        portfolio.total_value = portfolio.cash_balance + (quantity * price)
        self.db.flush()
        return position

    def _execute_sell(
        self,
        portfolio: Portfolio,
        account_id: str,
        market_pair_id: str,
        strategy_id: str,
        quantity: float,
        price: float,
        signal_id: str | None,
    ) -> tuple[Position, Trade]:
        position = self.positions.get_open(account_id, market_pair_id, strategy_id)
        if not position:
            raise ValidationError("No open paper position to sell")
        if quantity > position.quantity:
            raise ValidationError("Paper sell quantity exceeds open position")

        now = datetime.now(timezone.utc)
        proceeds = quantity * price
        gross_profit = (price - position.entry_price) * quantity
        profit_percentage = (gross_profit / (position.entry_price * quantity)) * 100 if position.entry_price else 0
        duration_minutes = int((now - position.opened_at).total_seconds() // 60)

        trade = Trade(
            position_id=position.id,
            strategy_id=strategy_id,
            entry_price=position.entry_price,
            exit_price=price,
            quantity=quantity,
            gross_profit=gross_profit,
            net_profit=gross_profit,
            profit_percentage=profit_percentage,
            duration_minutes=duration_minutes,
            opened_at=position.opened_at,
            closed_at=now,
        )
        self.trades.add(trade)

        position.quantity -= quantity
        position.current_price = price
        position.unrealized_pnl = 0
        if position.quantity == 0:
            position.status = "CLOSED"
            position.closed_at = now
        self.positions.update(position)

        portfolio.cash_balance += proceeds
        portfolio.total_value = portfolio.cash_balance + (position.quantity * price if position.status == "OPEN" else 0)
        return position, trade

    def _snapshot(self, portfolio: Portfolio) -> None:
        open_positions = self.db.query(Position).filter(Position.status == "OPEN").count()
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio.id,
            total_value=portfolio.total_value,
            cash_balance=portfolio.cash_balance,
            open_positions=open_positions,
            daily_pnl=0,
            total_pnl=0,
            captured_at=datetime.now(timezone.utc),
        )
        self.portfolio_snapshots.add(snapshot)

    def _log_risk_event(self, user_id: str, event_type: str, severity: str, description: str) -> None:
        self.risk_events.create(user_id=user_id, event_type=event_type, severity=severity, description=description)
        self.risk_events.commit()

    def _notify(self, user_id: str, notification_type: str, title: str, message: str) -> None:
        self.notifications.create(user_id=user_id, notification_type=notification_type, title=title, message=message)
        self.notifications.commit()

    def _require_paper_trading_enabled(self, user_id: str) -> None:
        try:
            self.feature_flags.require_enabled("paper_trading.enabled", environment=settings.app_env)
        except FeatureDisabledError as exc:
            audit = AuditLog(
                user_id=user_id,
                entity_type="feature_flag_enforcement",
                entity_id="paper_trading.enabled",
                action="PAPER_TRADING_BLOCKED",
                new_value={"flag_key": "paper_trading.enabled", "reason": str(exc.detail)},
            )
            self.db.add(audit)
            self.db.commit()
            logger.warning("paper trading blocked user_id=%s reason=%s", user_id, exc.detail)
            raise

    def _log_audit(self, user_id: str, entity_type: str, entity_id: str, action: str, details: dict[str, object]) -> None:
        audit = AuditLog(user_id=user_id, entity_type=entity_type, entity_id=entity_id, action=action, new_value=details)
        self.db.add(audit)
