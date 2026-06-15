from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.database.models.trading import Order, Signal, Strategy
from app.database.repositories.exchange_repository import ExchangeAccountRepository
from app.database.repositories.trading_repository import OrderRepository, SignalRepository, StrategyRepository

logger = logging.getLogger(__name__)


class StrategyService:
    def __init__(self, db: Session):
        self.db = db
        self.strategies = StrategyRepository(db)

    def create(self, name: str, code: str, version: str, strategy_type: str, description: str | None = None) -> Strategy:
        existing_strategy = self.strategies.get_by_code(code)
        if existing_strategy:
            raise ValidationError("Strategy code already exists")

        strategy = self.strategies.create(
            name=name,
            code=code,
            version=version,
            strategy_type=strategy_type,
            description=description,
        )
        self.strategies.commit()
        self.strategies.refresh(strategy)
        logger.info("Created strategy strategy_id=%s code=%s", strategy.id, strategy.code)
        return strategy

    def list(self, limit: int = 100, offset: int = 0) -> list[Strategy]:
        return self.strategies.list(limit=limit, offset=offset)


class SignalService:
    def __init__(self, db: Session):
        self.db = db
        self.signals = SignalRepository(db)
        self.strategies = StrategyRepository(db)

    def create(
        self,
        strategy_id: str,
        market_pair_id: str,
        signal_type: str,
        confidence: float,
        entry_price: float,
        stop_loss: float | None,
        take_profit: float | None,
        reason: str,
    ) -> Signal:
        if not self.strategies.get(strategy_id):
            raise NotFoundError("Strategy not found")
        if confidence < 0 or confidence > 100:
            raise ValidationError("Confidence must be between 0 and 100")

        signal = self.signals.create(
            strategy_id=strategy_id,
            market_pair_id=market_pair_id,
            signal_type=signal_type,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
            signal_time=datetime.now(timezone.utc),
            status="PENDING",
        )
        self.signals.commit()
        self.signals.refresh(signal)
        logger.info("Created signal signal_id=%s strategy_id=%s", signal.id, strategy_id)
        return signal

    def list(self, limit: int = 100) -> list[Signal]:
        return self.signals.latest(limit=limit)

    def get(self, signal_id: str) -> Signal:
        signal = self.signals.get(signal_id)
        if not signal:
            raise NotFoundError("Signal not found")
        return signal


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.accounts = ExchangeAccountRepository(db)

    def create_order(
        self,
        exchange_account_id: str,
        order_type: str,
        side: str,
        quantity: float,
        signal_id: str | None = None,
        price: float | None = None,
        status: str = "NEW",
        user_id: str | None = None,
    ) -> Order:
        if user_id is not None:
            account = self.accounts.get_by_user(user_id, exchange_account_id)
            if not account:
                raise NotFoundError("Exchange account not found for user")
            if account.status != "ACTIVE":
                raise ValidationError("Exchange account is not active")
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if price is not None and price <= 0:
            raise ValidationError("Price must be greater than zero")
        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValidationError("Order side must be BUY or SELL")

        order = self.orders.create(
            exchange_account_id=exchange_account_id,
            signal_id=signal_id,
            exchange_order_id=None,
            order_type=order_type,
            side=normalized_side,
            quantity=quantity,
            price=price,
            filled_quantity=0,
            status=status,
        )
        self.orders.commit()
        self.orders.refresh(order)
        logger.info("Created order order_id=%s account_id=%s", order.id, exchange_account_id)
        return order

    def list_orders(self, limit: int = 100, user_id: str | None = None) -> list[Order]:
        if user_id is not None:
            return self.orders.latest_by_user(user_id, limit=limit)
        return self.orders.latest(limit=limit)
