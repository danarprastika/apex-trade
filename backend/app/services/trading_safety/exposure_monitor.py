from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.database.models.trading import Position
from app.database.repositories.trading_safety_repository import ExposureLimitRepository
from app.domain.safety.value_objects import ValidationLayer

logger = logging.getLogger(__name__)


class ExposureMonitor:
    def __init__(self, db: Session, event_bus: Any | None = None):
        self.db = db
        self.exposure_limits = ExposureLimitRepository(db)
        self.event_bus = event_bus

    def check_user_exposure(
        self,
        user_id: str,
        symbol: str | None,
        proposed_quantity: float,
        proposed_price: float,
    ) -> tuple[bool, list[str]]:
        violations = []
        limits = self.exposure_limits.get_all_for_user(user_id, limit=100)

        for limit in limits:
            if limit.asset_id and symbol and self._matches_asset(symbol, limit.asset_id):
                proposed_value = proposed_quantity * proposed_price
                new_exposure = limit.current_exposure_percentage + proposed_value
                if new_exposure > limit.max_exposure_percentage:
                    violations.append(
                        f"Exposure limit exceeded for asset {limit.asset_id}: "
                        f"{limit.current_exposure_percentage}% + {proposed_value} > {limit.max_exposure_percentage}%",
                    )

        return len(violations) == 0, violations

    def update_exposure_actual(
        self,
        user_id: str,
        exchange_id: str | None,
        symbol: str | None,
        price: float,
    ) -> None:
        from app.database.models.exchange import ExchangeAccount

        query = (
            select(func.coalesce(func.sum(Position.quantity * Position.current_price), 0))
            .select_from(Position)
            .join(ExchangeAccount, Position.exchange_account_id == ExchangeAccount.id)
            .where(Position.status == "OPEN")
        )

        result = self.db.scalar(query)
        total_exposure = float(result or 0)

        if exchange_id:
            limit = self.exposure_limits.get_for_user(user_id, exchange_id=exchange_id)
            if limit:
                limit.current_exposure_percentage = total_exposure / 100
                self.exposure_limits.db.add(limit)
                self.exposure_limits.commit()

        if symbol:
            asset_id = self._get_asset_id(symbol)
            if asset_id:
                limit = self.exposure_limits.get_for_user(user_id, asset_id=asset_id)
                if limit:
                    limit.current_exposure_percentage = total_exposure / 100
                    self.exposure_limits.db.add(limit)
                    self.exposure_limits.commit()

    def set_limit(
        self,
        user_id: str,
        scope: str,
        max_exposure_percentage: float,
        exchange_id: str | None = None,
        asset_id: str | None = None,
    ) -> Any:
        if max_exposure_percentage <= 0 or max_exposure_percentage > 100:
            raise ValidationError("Exposure percentage must be between 0 and 100")

        existing = self.exposure_limits.get_for_user(user_id, exchange_id, asset_id)
        if existing:
            existing.max_exposure_percentage = max_exposure_percentage
            self.exposure_limits.db.add(existing)
        else:
            from app.database.models.trading_safety import ExposureLimit
            existing = ExposureLimit(
                user_id=user_id,
                exchange_id=exchange_id,
                asset_id=asset_id,
                scope=scope,
                max_exposure_percentage=max_exposure_percentage,
            )
            self.exposure_limits.db.add(existing)

        self.exposure_limits.commit()
        self.exposure_limits.refresh(existing)
        return existing

    def _matches_asset(self, symbol: str, asset_id: str) -> bool:
        return symbol.replace("USDT", "").replace("USD", "") in asset_id


class ExposureLimitService:
    def __init__(self, db: Session):
        self.db = db
        self.monitor = ExposureMonitor(db)

    def check_and_update(
        self,
        user_id: str,
        exchange_id: str | None = None,
        symbol: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
    ) -> None:
        if quantity and price:
            compliant, violations = self.monitor.check_user_exposure(user_id, symbol, quantity, price)
            if not compliant:
                from app.core.exceptions import ValidationError
                raise ValidationError(f"Exposure limit violations: {'; '.join(violations)}")