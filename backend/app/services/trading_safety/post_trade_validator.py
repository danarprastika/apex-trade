from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.database.repositories.risk_repository import RiskEventRepository
from app.database.repositories.trading_repository import OrderRepository
from app.domain.safety.value_objects import SafetyDecision, ValidationLayer

logger = logging.getLogger(__name__)


class PostTradeValidator:
    def __init__(
        self,
        db: Session,
        event_bus: Any | None = None,
    ):
        self.db = db
        self.orders = OrderRepository(db)
        self.risk_events = RiskEventRepository(db)
        self.event_bus = event_bus

    def validate(
        self,
        order_id: str,
        adapter: Any,
        context: Any,
    ) -> SafetyDecision:
        decision = SafetyDecision(approved=True, reasons=[], checks_performed={}, execution_blocked_by=[])

        order = self.orders.get(order_id)
        if not order:
            decision.add_rejection(ValidationLayer.ORDER_SIZE_LIMIT, f"Order {order_id} not found")
            return decision

        try:
            exchange_order = adapter.fetch_order(order_id=str(order.exchange_order_id), context=context)
        except Exception as e:
            decision.add_rejection(ValidationLayer.KILL_SWITCH, f"Exchange fetch failed: {e}")
            return decision

        self._validate_fill_price(order, exchange_order, decision)
        self._validate_fees(order, exchange_order, decision)
        self._validate_status(order, exchange_order, decision)

        if not decision.approved:
            self._log_validation_result(context.user_id, decision)

        return decision

    def _validate_fill_price(
        self,
        order: Any,
        exchange_order: Any,
        decision: SafetyDecision,
    ) -> None:
        if not exchange_order or not exchange_order.average_fill_price:
            return

        expected_price = float(order.price) if order.price else None
        actual_price = float(exchange_order.average_fill_price)

        if expected_price and actual_price:
            price_deviation_pct = abs(expected_price - actual_price) / expected_price * 100
            if price_deviation_pct > 2.0:
                decision.add_rejection(
                    ValidationLayer.MARKET_DATA_QUALITY,
                    f"Fill price deviation {price_deviation_pct:.2f}% exceeds 2% threshold",
                )

    def _validate_fees(
        self,
        order: Any,
        exchange_order: Any,
        decision: SafetyDecision,
    ) -> None:
        if not exchange_order:
            return

        exchange_fee = float(exchange_order.fee) if exchange_order.fee else None
        if exchange_fee is not None and exchange_fee > 0:
            decision.add_success(ValidationLayer.EXPOSURE_LIMIT)

    def _validate_status(
        self,
        order: Any,
        exchange_order: Any,
        decision: SafetyDecision,
    ) -> None:
        if not exchange_order:
            return

        actual_status = exchange_order.status.lower() if exchange_order.status else None
        expected_status = order.status.lower() if order.status else None

        if expected_status and actual_status and expected_status != actual_status and expected_status == "filled" and actual_status not in ("filled", "closed"):
            decision.add_rejection(
                ValidationLayer.DAILY_LOSS_LIMIT,
                f"Order status mismatch: expected {expected_status}, actual {actual_status}",
            )

    def _log_validation_result(self, user_id: str, decision: SafetyDecision) -> None:
        self.risk_events.create(
            user_id=user_id,
            event_type="POSTTRADE_REJECTED",
            severity="HIGH",
            description="; ".join(decision.reasons),
        )
