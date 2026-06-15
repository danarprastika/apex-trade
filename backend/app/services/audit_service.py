from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.database.models.audit import AuditLog
from app.database.repositories.audit_repository import AuditLogRepository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.logs = AuditLogRepository(db)

    def log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: str | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        audit = self.logs.create(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self.logs.commit()
        self.logs.refresh(audit)
        logger.info("Audit log entity_type=%s entity_id=%s action=%s", entity_type, entity_id, action)
        return audit

    def list_by_user(self, user_id: str, limit: int = 100) -> list[AuditLog]:
        return self.logs.list_by_user(user_id, limit=limit)

    def list_all(self, limit: int = 100) -> list[AuditLog]:
        return self.logs.list_all(limit=limit)
