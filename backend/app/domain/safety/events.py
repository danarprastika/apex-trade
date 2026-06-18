from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.events.types import ApexEvent


class TradingSafetyEventTypes:
    KILLSWITCH_TRIGGERED = "KILLSWITCH_TRIGGERED"
    KILLSWITCH_CLEARED = "KILLSWITCH_CLEARED"
    PRETRADE_VALIDATED = "PRETRADE_VALIDATED"
    PRETRADE_REJECTED = "PRETRADE_REJECTED"
    POSTTRADE_VALIDATED = "POSTTRADE_VALIDATED"
    POSTTRADE_DISCREPANCY = "POSTTRADE_DISCREPANCY"
    RECONCILIATION_ORDER_COMPLETED = "RECONCILIATION_ORDER_COMPLETED"
    RECONCILIATION_POSITION_COMPLETED = "RECONCILIATION_POSITION_COMPLETED"
    MARKET_DATA_QUALITY_CHECK = "MARKET_DATA_QUALITY_CHECK"
    MARKET_DATA_QUALITY_FAILED = "MARKET_DATA_QUALITY_FAILED"
    EXPOSURE_LIMIT_TRIGGERED = "EXPOSURE_LIMIT_TRIGGERED"


@dataclass
class KillSwitchTriggered(ApexEvent):
    scope: str = ""
    scope_id: str | None = None
    reason: str | None = None
    triggered_by: str | None = None

    def __post_init__(self):
        self.type = TradingSafetyEventTypes.KILLSWITCH_TRIGGERED
        self.payload = {
            "scope": self.scope,
            "scope_id": self.scope_id,
            "reason": self.reason,
            "triggered_by": self.triggered_by,
        }


@dataclass
class KillSwitchCleared(ApexEvent):
    scope: str = ""
    scope_id: str | None = None
    cleared_by: str | None = None

    def __post_init__(self):
        self.type = TradingSafetyEventTypes.KILLSWITCH_CLEARED
        self.payload = {
            "scope": self.scope,
            "scope_id": self.scope_id,
            "cleared_by": self.cleared_by,
        }


@dataclass
class PreTradeValidated(ApexEvent):
    user_id: str = ""
    order_id: str | None = None
    validations_passed: list[str] = None
    safety_decision_id: str | None = None

    def __post_init__(self):
        if self.validations_passed is None:
            self.validations_passed = []
        self.type = TradingSafetyEventTypes.PRETRADE_VALIDATED
        self.payload = {
            "user_id": self.user_id,
            "order_id": self.order_id,
            "validations_passed": self.validations_passed,
            "safety_decision_id": self.safety_decision_id,
        }


@dataclass
class PreTradeRejected(ApexEvent):
    user_id: str = ""
    order_id: str | None = None
    rejection_reasons: list[str] = None
    safety_context: dict[str, Any] = None

    def __post_init__(self):
        if self.rejection_reasons is None:
            self.rejection_reasons = []
        if self.safety_context is None:
            self.safety_context = {}
        self.type = TradingSafetyEventTypes.PRETRADE_REJECTED
        self.payload = {
            "user_id": self.user_id,
            "order_id": self.order_id,
            "rejection_reasons": self.rejection_reasons,
            "safety_context": self.safety_context,
        }


@dataclass
class OrderReconciliationCompleted(ApexEvent):
    order_id: str = ""
    user_id: str = ""
    exchange_id: str = ""
    discrepancies_found: bool = False
    actions_taken: list[str] = None

    def __post_init__(self):
        if self.actions_taken is None:
            self.actions_taken = []
        self.type = TradingSafetyEventTypes.RECONCILIATION_ORDER_COMPLETED
        self.payload = {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "exchange_id": self.exchange_id,
            "discrepancies_found": self.discrepancies_found,
            "actions_taken": self.actions_taken,
        }


@dataclass
class PositionReconciliationCompleted(ApexEvent):
    position_id: str = ""
    user_id: str = ""
    exchange_id: str = ""
    discrepancies_found: bool = False
    actions_taken: list[str] = None

    def __post_init__(self):
        if self.actions_taken is None:
            self.actions_taken = []
        self.type = TradingSafetyEventTypes.RECONCILIATION_POSITION_COMPLETED
        self.payload = {
            "position_id": self.position_id,
            "user_id": self.user_id,
            "exchange_id": self.exchange_id,
            "discrepancies_found": self.discrepancies_found,
            "actions_taken": self.actions_taken,
        }


@dataclass
class PostTradeValidated(ApexEvent):
    user_id: str = ""
    order_id: str = ""
    validation_passed: bool = True
    checks_performed: list[str] = None

    def __post_init__(self):
        if self.checks_performed is None:
            self.checks_performed = []
        self.type = TradingSafetyEventTypes.POSTTRADE_VALIDATED
        self.payload = {
            "user_id": self.user_id,
            "order_id": self.order_id,
            "validation_passed": self.validation_passed,
            "checks_performed": self.checks_performed,
        }


@dataclass
class PostTradeDiscrepancy(ApexEvent):
    user_id: str = ""
    order_id: str = ""
    discrepancy_type: str = ""
    details: dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        self.type = TradingSafetyEventTypes.POSTTRADE_DISCREPANCY
        self.payload = {
            "user_id": self.user_id,
            "order_id": self.order_id,
            "discrepancy_type": self.discrepancy_type,
            "details": self.details,
        }