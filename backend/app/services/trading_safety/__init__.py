from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.domain.safety.value_objects import SafetyContext, SafetyDecision
from app.integrations.exchanges.failover.manager import ExchangeFailoverManager
from app.services.trading_safety.exposure_monitor import ExposureMonitor
from app.services.trading_safety.kill_switch_service import KillSwitchService
from app.services.trading_safety.market_data_quality import MarketDataQualityEngine
from app.services.trading_safety.order_reconciliation import OrderReconciliationService
from app.services.trading_safety.position_reconciliation import PositionReconciliationService
from app.services.trading_safety.post_trade_validator import PostTradeValidator
from app.services.trading_safety.pre_trade_validator import PreTradeValidator

__all__ = [
    "SafetyOrchestrator",
    "KillSwitchService",
    "PreTradeValidator",
    "PostTradeValidator",
    "MarketDataQualityEngine",
    "OrderReconciliationService",
    "PositionReconciliationService",
    "ExposureMonitor",
]

logger = logging.getLogger(__name__)


class SafetyOrchestrator:
    def __init__(
        self,
        db: Session,
        kill_switch_service: KillSwitchService | None = None,
        pre_trade_validator: PreTradeValidator | None = None,
        post_trade_validator: PostTradeValidator | None = None,
        market_data_quality: MarketDataQualityEngine | None = None,
        order_reconciliation: OrderReconciliationService | None = None,
        position_reconciliation: PositionReconciliationService | None = None,
        exchange_failover: ExchangeFailoverManager | None = None,
        event_bus: Any | None = None,
    ):
        self.db = db
        self.kill_switch = kill_switch_service or KillSwitchService(db, event_bus)
        self.pre_trade_validator = pre_trade_validator or PreTradeValidator(db, self.kill_switch, None, event_bus)
        self.post_trade_validator = post_trade_validator or PostTradeValidator(db, event_bus)
        self.market_data_quality = market_data_quality or MarketDataQualityEngine(db, event_bus)
        self.order_reconciliation = order_reconciliation or OrderReconciliationService(db, event_bus)
        self.position_reconciliation = position_reconciliation or PositionReconciliationService(db, event_bus)
        self.exchange_failover = exchange_failover or ExchangeFailoverManager()
        self.event_bus = event_bus

    def validate_pre_trade(self, context: SafetyContext) -> SafetyDecision:
        decision = self.pre_trade_validator.validate(context)

        if not decision.approved:
            logger.warning(
                "Pre-trade validation rejected user_id=%s symbol=%s reasons=%s",
                context.user_id, context.symbol, decision.reasons,
            )
        else:
            logger.info(
                "Pre-trade validation approved user_id=%s symbol=%s",
                context.user_id, context.symbol,
            )

        return decision

    def should_failover_exchange(
        self,
        exchange_id: str,
        operation: str,
        context: dict[str, Any],
    ) -> bool:
        return self.exchange_failover.evaluate_failover(operation, context).should_failover

    def reconcile_order(self, order_id: str, adapter: Any, context: Any) -> dict[str, Any]:
        return self.order_reconciliation.reconcile_order(order_id, adapter, context)

    def reconcile_position(self, position_id: str, adapter: Any, context: Any) -> dict[str, Any]:
        return self.position_reconciliation.reconcile_position(position_id, adapter, context)

    def check_market_data_quality(self, data: Any, data_type: str, market_pair_id: str, exchange_id: str) -> tuple[bool, float, list[str]]:
        if data_type == "candle":
            return self.market_data_quality.evaluate_candle_quality(data, market_pair_id, exchange_id)
        elif data_type == "ticker":
            return self.market_data_quality.evaluate_ticker_quality(data, market_pair_id, exchange_id)
        elif data_type == "order_book":
            return self.market_data_quality.evaluate_order_book_quality(data, market_pair_id, exchange_id)
        return True, 1.0, []

    def validate_post_trade(
        self,
        order_id: str,
        adapter: Any,
        context: Any,
    ) -> SafetyDecision:
        decision = self.post_trade_validator.validate(order_id, adapter, context)

        if not decision.approved:
            logger.warning(
                "Post-trade validation rejected order_id=%s reasons=%s",
                order_id, decision.reasons,
            )
        else:
            logger.info(
                "Post-trade validation passed order_id=%s",
                order_id,
            )

        return decision

    def get_health_status(self) -> dict[str, Any]:
        kill_switch_healthy = self._check_kill_switch_health()
        reconciliation_healthy = self._check_reconciliation_health()
        market_data_healthy = self._check_market_data_health()
        exposure_healthy = self._check_exposure_health()

        all_healthy = kill_switch_healthy and reconciliation_healthy and market_data_healthy and exposure_healthy

        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": {
                "kill_switch": {"status": "healthy" if kill_switch_healthy else "unhealthy"},
                "reconciliation": {"status": "healthy" if reconciliation_healthy else "unhealthy"},
                "market_data_quality": {"status": "healthy" if market_data_healthy else "unhealthy"},
                "exposure_monitor": {"status": "healthy" if exposure_healthy else "unhealthy"},
            },
        }

    def _check_kill_switch_health(self) -> bool:
        try:
            self.kill_switch.is_global_kill_enabled()
            return True
        except Exception:
            return False

    def _check_reconciliation_health(self) -> bool:
        return True

    def _check_market_data_health(self) -> bool:
        return True

    def _check_exposure_health(self) -> bool:
        return True
