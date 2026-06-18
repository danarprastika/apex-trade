from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError, ValidationError
from app.database.repositories.trading_safety_repository import (
    KillSwitchAuditLogRepository,
    KillSwitchStateRepository,
)
from app.domain.safety.events import (
    KillSwitchCleared,
    KillSwitchTriggered,
    TradingSafetyEventTypes,
)
from app.domain.safety.value_objects import KillSwitchScope, SafetyDecision, ValidationLayer

logger = logging.getLogger(__name__)


class KillSwitchService:
    def __init__(self, db: Session, event_bus: Any | None = None):
        self.db = db
        self.kill_states = KillSwitchStateRepository(db)
        self.kill_audit = KillSwitchAuditLogRepository(db)
        self.event_bus = event_bus

    def is_global_kill_enabled(self) -> bool:
        state = self.kill_states.get_active(KillSwitchScope.GLOBAL.value)
        return state is not None and state.enabled and not self._is_expired(state)

    def is_user_kill_enabled(self, user_id: str) -> bool:
        state = self.kill_states.get_active(KillSwitchScope.USER.value, user_id)
        return state is not None and state.enabled and not self._is_expired(state)

    def is_exchange_kill_enabled(self, exchange_id: str) -> bool:
        state = self.kill_states.get_active(KillSwitchScope.EXCHANGE.value, exchange_id)
        return state is not None and state.enabled and not self._is_expired(state)

    def is_strategy_kill_enabled(self, strategy_id: str) -> bool:
        state = self.kill_states.get_active(KillSwitchScope.STRATEGY.value, strategy_id)
        return state is not None and state.enabled and not self._is_expired(state)

    def check_all(self, user_id: str | None, exchange_id: str | None, strategy_id: str | None) -> tuple[bool, list[str]]:
        blocked = []
        if self.is_global_kill_enabled():
            blocked.append("GLOBAL")
        if user_id and self.is_user_kill_enabled(user_id):
            blocked.append(f"USER:{user_id}")
        if exchange_id and self.is_exchange_kill_enabled(exchange_id):
            blocked.append(f"EXCHANGE:{exchange_id}")
        if strategy_id and self.is_strategy_kill_enabled(strategy_id):
            blocked.append(f"STRATEGY:{strategy_id}")
        return len(blocked) > 0, blocked

    def trigger_kill(
        self,
        scope: KillSwitchScope,
        scope_id: str | None,
        triggered_by: str,
        actor_role: str,
        ip_address: str | None,
        reason: str | None,
        expires_at: datetime | None,
    ) -> None:
        self._authorize_kill_trigger(scope, actor_role, scope_id, triggered_by)

        old_state = self.kill_states.get_active(scope.value, scope_id)
        old_value = {
            "enabled": old_state.enabled if old_state else False,
            "reason": old_state.reason if old_state else None,
        }

        try:
            state = self.kill_states.set_state(
                scope=scope.value,
                scope_id=scope_id,
                enabled=True,
                reason=reason,
                triggered_by=triggered_by,
                expires_at=expires_at,
            )
            self.kill_states.commit()
            self.kill_states.refresh(state)
        except Exception:
            self.kill_states.rollback()
            raise

        self.kill_audit.log_action(
            scope=scope.value,
            scope_id=scope_id,
            action="trigger",
            old_value=old_value,
            new_value={"enabled": True, "reason": reason, "expires_at": expires_at},
            actor_user_id=triggered_by,
            actor_role=actor_role,
            ip_address=ip_address,
            reason=reason,
        )
        self.kill_audit.commit()

        if self.event_bus:
            event = KillSwitchTriggered(
                scope=scope.value,
                scope_id=scope_id,
                reason=reason,
                triggered_by=triggered_by,
            )
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.event_bus.publish(event))
            except RuntimeError:
                pass

        logger.warning(
            "Kill switch triggered scope=%s scope_id=%s reason=%s",
            scope.value, scope_id, reason,
        )

    def clear_kill(
        self,
        scope: KillSwitchScope,
        scope_id: str | None,
        cleared_by: str,
        actor_role: str,
        ip_address: str | None,
        reason: str | None,
    ) -> None:
        if scope == KillSwitchScope.GLOBAL and actor_role != "SUPER_ADMIN":
            raise PermissionDeniedError("Only SUPER_ADMIN can clear global kill switch")

        old_state = self.kill_states.get_active(scope.value, scope_id)
        old_value = {
            "enabled": old_state.enabled if old_state else False,
            "reason": old_state.reason if old_state else None,
        }

        try:
            if old_state:
                old_state.enabled = False
                self.kill_states.db.add(old_state)
                self.kill_states.commit()
            else:
                self.kill_states.rollback()
        except Exception:
            self.kill_states.rollback()
            raise

        self.kill_audit.log_action(
            scope=scope.value,
            scope_id=scope_id,
            action="clear",
            old_value=old_value,
            new_value={"enabled": False, "reason": reason},
            actor_user_id=cleared_by,
            actor_role=actor_role,
            ip_address=ip_address,
            reason=reason,
        )
        self.kill_audit.commit()

        if self.event_bus:
            event = KillSwitchCleared(
                scope=scope.value,
                scope_id=scope_id,
                cleared_by=cleared_by,
            )
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.event_bus.publish(event))
            except RuntimeError:
                pass

        logger.info(
            "Kill switch cleared scope=%s scope_id=%s by=%s",
            scope.value, scope_id, cleared_by,
        )

    def _authorize_kill_trigger(self, scope: KillSwitchScope, actor_role: str, scope_id: str | None, triggered_by: str | None = None) -> None:
        if scope == KillSwitchScope.GLOBAL and actor_role != "SUPER_ADMIN":
            raise PermissionDeniedError("Only SUPER_ADMIN can trigger global kill switch")
        if scope == KillSwitchScope.USER and actor_role not in ("ADMIN", "SUPER_ADMIN", "TRADER"):
            raise PermissionDeniedError("Only ADMIN or self can trigger user kill switch")
        if scope == KillSwitchScope.USER and actor_role == "TRADER" and triggered_by and scope_id and triggered_by != scope_id:
            raise PermissionDeniedError("TRADER can only trigger their own user kill switch")
        if scope == KillSwitchScope.EXCHANGE and actor_role != "ADMIN":
            raise PermissionDeniedError("Only ADMIN can trigger exchange kill switch")
        if scope == KillSwitchScope.STRATEGY and actor_role not in ("ADMIN", "SUPER_ADMIN"):
            raise PermissionDeniedError("Only ADMIN can trigger strategy kill switch")

    def _is_expired(self, state: Any) -> bool:
        if state.expires_at is None:
            return False
        from datetime import timezone
        now = datetime.now(timezone.utc) if state.expires_at.tzinfo else datetime.now()
        expires_at_naive = state.expires_at.replace(tzinfo=None) if state.expires_at.tzinfo else state.expires_at
        now_naive = now.replace(tzinfo=None) if now.tzinfo else now
        return now_naive > expires_at_naive