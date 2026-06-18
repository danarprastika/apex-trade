from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database.models.trading_safety import (
    KillSwitchAuditLog,
    KillSwitchState,
    MarketDataQualityEvent,
    OrderReconciliationLog,
    PositionReconciliationLog,
    ExposureLimit,
)
from app.database.repositories.base import BaseRepository


class KillSwitchStateRepository(BaseRepository[KillSwitchState]):
    def __init__(self, db: Session):
        super().__init__(db, KillSwitchState)

    def get_active(self, scope: str, scope_id: str | None = None) -> KillSwitchState | None:
        statement = select(KillSwitchState).where(
            (KillSwitchState.scope == scope)
            & (KillSwitchState.enabled == True)
        )
        if scope_id is not None:
            statement = statement.where(KillSwitchState.scope_id == scope_id)
        else:
            statement = statement.where(KillSwitchState.scope_id.is_(None))
        return self.db.scalar(statement)

    def list_by_scope(self, scope: str, limit: int = 100) -> list[KillSwitchState]:
        return list(
            self.db.scalars(
                select(KillSwitchState)
                .where(KillSwitchState.scope == scope)
                .limit(limit)
            ).all()
        )

    def set_state(
        self,
        scope: str,
        scope_id: str | None,
        enabled: bool,
        reason: str | None,
        triggered_by: str | None,
        expires_at: datetime | None = None,
    ) -> KillSwitchState:
        existing = self.get_active(scope, scope_id)
        if existing:
            existing.enabled = enabled
            existing.reason = reason
            existing.triggered_by = triggered_by
            existing.expires_at = expires_at
            self.db.add(existing)
        else:
            existing = KillSwitchState(
                scope=scope,
                scope_id=scope_id,
                enabled=enabled,
                reason=reason,
                triggered_by=triggered_by,
                expires_at=expires_at,
            )
            self.db.add(existing)
        return existing


class KillSwitchAuditLogRepository(BaseRepository[KillSwitchAuditLog]):
    def __init__(self, db: Session):
        super().__init__(db, KillSwitchAuditLog)

    def log_action(
        self,
        scope: str,
        scope_id: str | None,
        action: str,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
        actor_user_id: str | None,
        actor_role: str | None,
        ip_address: str | None,
        reason: str | None,
    ) -> KillSwitchAuditLog:
        log = KillSwitchAuditLog(
            scope=scope,
            scope_id=scope_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            ip_address=ip_address,
            reason=reason,
        )
        self.db.add(log)
        return log

    def list_by_scope(self, scope: str, limit: int = 100) -> list[KillSwitchAuditLog]:
        return list(
            self.db.scalars(
                select(KillSwitchAuditLog)
                .where(KillSwitchAuditLog.scope == scope)
                .order_by(KillSwitchAuditLog.created_at.desc())
                .limit(limit)
            ).all()
        )


class OrderReconciliationLogRepository(BaseRepository[OrderReconciliationLog]):
    def __init__(self, db: Session):
        super().__init__(db, OrderReconciliationLog)

    def log_discrepancy(
        self,
        order_id: str,
        exchange_id: str,
        user_id: str,
        expected_status: str,
        actual_status: str,
        discrepancy_detected: bool,
        resolution_action: str | None,
        resolution_details: dict[str, Any] | None,
    ) -> OrderReconciliationLog:
        log = OrderReconciliationLog(
            order_id=order_id,
            exchange_id=exchange_id,
            user_id=user_id,
            expected_status=expected_status,
            actual_status=actual_status,
            discrepancy_detected=discrepancy_detected,
            resolution_action=resolution_action,
            resolution_details=resolution_details,
        )
        self.db.add(log)
        return log

    def list_unresolved(self, limit: int = 100) -> list[OrderReconciliationLog]:
        return list(
            self.db.scalars(
                select(OrderReconciliationLog)
                .where(OrderReconciliationLog.resolved_at.is_(None))
                .limit(limit)
            ).all()
        )


class PositionReconciliationLogRepository(BaseRepository[PositionReconciliationLog]):
    def __init__(self, db: Session):
        super().__init__(db, PositionReconciliationLog)

    def log_discrepancy(
        self,
        position_id: str,
        exchange_id: str,
        user_id: str,
        expected_quantity: float | None,
        actual_quantity: float | None,
        quantity_discrepancy: float | None,
        expected_entry_price: float | None,
        actual_entry_price: float | None,
        price_discrepancy: float | None,
        discrepancy_detected: bool,
        resolution_action: str | None,
        resolution_details: dict[str, Any] | None,
    ) -> PositionReconciliationLog:
        log = PositionReconciliationLog(
            position_id=position_id,
            exchange_id=exchange_id,
            user_id=user_id,
            expected_quantity=expected_quantity,
            actual_quantity=actual_quantity,
            quantity_discrepancy=quantity_discrepancy,
            expected_entry_price=expected_entry_price,
            actual_entry_price=actual_entry_price,
            price_discrepancy=price_discrepancy,
            discrepancy_detected=discrepancy_detected,
            resolution_action=resolution_action,
            resolution_details=resolution_details,
        )
        self.db.add(log)
        return log

    def list_unresolved(self, limit: int = 100) -> list[PositionReconciliationLog]:
        return list(
            self.db.scalars(
                select(PositionReconciliationLog)
                .where(PositionReconciliationLog.resolved_at.is_(None))
                .limit(limit)
            ).all()
        )


class MarketDataQualityEventRepository(BaseRepository[MarketDataQualityEvent]):
    def __init__(self, db: Session):
        super().__init__(db, MarketDataQualityEvent)

    def log_quality_check(
        self,
        market_pair_id: str,
        exchange_id: str,
        data_type: str,
        quality_score: float | None,
        issues: dict[str, Any] | None,
        is_valid: bool,
    ) -> MarketDataQualityEvent:
        event = MarketDataQualityEvent(
            market_pair_id=market_pair_id,
            exchange_id=exchange_id,
            data_type=data_type,
            quality_score=quality_score,
            issues=issues,
            is_valid=is_valid,
        )
        self.db.add(event)
        return event

    def latest_for_symbol(
        self, market_pair_id: str, exchange_id: str, data_type: str, minutes: int = 5
    ) -> MarketDataQualityEvent | None:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return self.db.scalar(
            select(MarketDataQualityEvent)
            .where(
                (MarketDataQualityEvent.market_pair_id == market_pair_id)
                & (MarketDataQualityEvent.exchange_id == exchange_id)
                & (MarketDataQualityEvent.data_type == data_type)
                & (MarketDataQualityEvent.created_at >= cutoff)
            )
            .order_by(MarketDataQualityEvent.created_at.desc())
        )


class ExposureLimitRepository(BaseRepository[ExposureLimit]):
    def __init__(self, db: Session):
        super().__init__(db, ExposureLimit)

    def get_for_user(
        self,
        user_id: str,
        exchange_id: str | None = None,
        asset_id: str | None = None,
    ) -> ExposureLimit | None:
        statement = select(ExposureLimit).where(ExposureLimit.user_id == user_id)
        if exchange_id is not None:
            statement = statement.where(ExposureLimit.exchange_id == exchange_id)
        if asset_id is not None:
            statement = statement.where(ExposureLimit.asset_id == asset_id)
        return self.db.scalar(statement)

    def get_all_for_user(self, user_id: str, limit: int = 100) -> list[ExposureLimit]:
        return list(
            self.db.scalars(
                select(ExposureLimit)
                .where(ExposureLimit.user_id == user_id)
                .limit(limit)
            ).all()
        )

    def update_exposure(self, limit_id: str, current_percentage: float) -> ExposureLimit:
        limit = self.get(limit_id)
        if limit:
            limit.current_exposure_percentage = current_percentage
            self.db.add(limit)
        return limit

    def calculate_current_exposure(self, user_id: str, exchange_id: str | None, asset_id: str | None) -> float:
        from app.database.models.trading import Position
        from app.database.models.exchange import ExchangeAccount

        query = (
            select(func.coalesce(func.sum(Position.quantity * Position.current_price), 0))
            .select_from(Position)
            .join(ExchangeAccount, Position.exchange_account_id == ExchangeAccount.id)
            .where(ExchangeAccount.user_id == user_id)
        )
        if exchange_id is not None:
            query = query.where(ExchangeAccount.exchange_id == exchange_id)
        if asset_id is not None:
            query = query.where(Position.market_pair_id == asset_id)

        result = self.db.scalar(query)
        return float(result or 0)