from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.database.models.trading import Position
from app.database.repositories.trading_repository import PositionRepository
from app.database.repositories.trading_safety_repository import PositionReconciliationLogRepository
from app.integrations.exchanges.interfaces import ExchangeAdapter

logger = logging.getLogger(__name__)


class PositionReconciliationService:
    def __init__(self, db: Session, event_bus: Any | None = None):
        self.db = db
        self.positions = PositionRepository(db)
        self.reconciliation_logs = PositionReconciliationLogRepository(db)
        self.event_bus = event_bus

    async def reconcile_position(
        self,
        position_id: str,
        adapter: ExchangeAdapter,
        context: Any,
    ) -> dict[str, Any]:
        position = self.positions.get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")

        discrepancies = []
        try:
            exchange_positions = adapter.fetch_positions(context=context)
            exchange_position = next(
                (p for p in exchange_positions if p.source_symbol == position.symbol),
                None,
            )

            actual_quantity = float(exchange_position.quantity) if exchange_position else 0
            actual_entry_price = float(exchange_position.entry_price) if exchange_position else None

            qty_discrepancy = abs(float(position.quantity) - actual_quantity)
            if qty_discrepancy > 0.0001:
                discrepancies.append({
                    "field": "quantity",
                    "expected": float(position.quantity),
                    "actual": actual_quantity,
                    "discrepancy": qty_discrepancy,
                })

            if exchange_position and position.entry_price and actual_entry_price:
                price_discrepancy = abs(float(position.entry_price) - actual_entry_price)
                if price_discrepancy > 0.01:
                    discrepancies.append({
                        "field": "entry_price",
                        "expected": float(position.entry_price),
                        "actual": actual_entry_price,
                        "discrepancy": price_discrepancy,
                    })

            log = self.reconciliation_logs.log_discrepancy(
                position_id=position_id,
                exchange_id=context.exchange_id,
                user_id=context.user_id,
                expected_quantity=float(position.quantity),
                actual_quantity=actual_quantity,
                quantity_discrepancy=qty_discrepancy if qty_discrepancy > 0.0001 else None,
                expected_entry_price=float(position.entry_price) if position.entry_price else None,
                actual_entry_price=actual_entry_price,
                price_discrepancy=price_discrepancy if exchange_position and position.entry_price else None,
                discrepancy_detected=len(discrepancies) > 0,
                resolution_action="sync" if discrepancies else None,
                resolution_details={"actions": ["sync_position_state"]} if discrepancies else None,
            )
            self.reconciliation_logs.commit()

            if discrepancies:
                self._handle_discrepancies(position, discrepancies)

            return {
                "position_id": position_id,
                "discrepancies_found": len(discrepancies) > 0,
                "discrepancies": discrepancies,
            }
        except Exception as e:
            logger.exception("Position reconciliation failed for position_id=%s", position_id)
            self.reconciliation_logs.log_discrepancy(
                position_id=position_id,
                exchange_id=context.exchange_id,
                user_id=context.user_id,
                expected_quantity=None,
                actual_quantity=None,
                quantity_discrepancy=None,
                expected_entry_price=None,
                actual_entry_price=None,
                price_discrepancy=None,
                discrepancy_detected=True,
                resolution_action="retry",
                resolution_details={"error": str(e)},
            )
            self.reconciliation_logs.commit()
            return {
                "position_id": position_id,
                "discrepancies_found": True,
                "error": str(e),
            }

    def _handle_discrepancies(self, position: Position, discrepancies: list[dict]) -> None:
        logger.warning(
            "Position discrepancies detected position_id=%s discrepancies=%s",
            position.id, discrepancies,
        )