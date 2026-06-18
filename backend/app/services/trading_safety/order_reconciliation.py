from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.database.models.trading import Order
from app.database.repositories.trading_repository import OrderRepository
from app.database.repositories.trading_safety_repository import OrderReconciliationLogRepository
from app.integrations.exchanges.interfaces import ExchangeAdapter

logger = logging.getLogger(__name__)


class OrderReconciliationService:
    def __init__(self, db: Session, event_bus: Any | None = None):
        self.db = db
        self.orders = OrderRepository(db)
        self.reconciliation_logs = OrderReconciliationLogRepository(db)
        self.event_bus = event_bus

    async def reconcile_order(
        self,
        order_id: str,
        adapter: ExchangeAdapter,
        context: Any,
    ) -> dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        discrepancies = []
        try:
            exchange_order = adapter.fetch_order(order_id=str(order.exchange_order_id), context=context)
            actual_status = exchange_order.status if exchange_order else None

            if order.status != actual_status:
                discrepancies.append({
                    "field": "status",
                    "expected": order.status,
                    "actual": actual_status,
                })

            if exchange_order and order.filled_quantity != float(exchange_order.filled_quantity or 0):
                discrepancies.append({
                    "field": "filled_quantity",
                    "expected": order.filled_quantity,
                    "actual": exchange_order.filled_quantity,
                })

            log = self.reconciliation_logs.log_discrepancy(
                order_id=order_id,
                exchange_id=context.exchange_id,
                user_id=context.user_id,
                expected_status=order.status,
                actual_status=actual_status,
                discrepancy_detected=len(discrepancies) > 0,
                resolution_action="sync" if discrepancies else None,
                resolution_details={"actions": ["sync_order_state"]} if discrepancies else None,
            )
            self.reconciliation_logs.commit()

            if discrepancies:
                self._handle_discrepancies(order, discrepancies)

            return {
                "order_id": order_id,
                "discrepancies_found": len(discrepancies) > 0,
                "discrepancies": discrepancies,
            }
        except Exception as e:
            logger.exception("Order reconciliation failed for order_id=%s", order_id)
            self.reconciliation_logs.log_discrepancy(
                order_id=order_id,
                exchange_id=context.exchange_id,
                user_id=context.user_id,
                expected_status=order.status,
                actual_status=None,
                discrepancy_detected=True,
                resolution_action="retry",
                resolution_details={"error": str(e)},
            )
            self.reconciliation_logs.commit()
            return {
                "order_id": order_id,
                "discrepancies_found": True,
                "error": str(e),
            }

    def _handle_discrepancies(self, order: Order, discrepancies: list[dict]) -> None:
        logger.warning(
            "Order discrepancies detected order_id=%s discrepancies=%s",
            order.id, discrepancies,
        )