from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.audit import AuditLog
from app.database.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(db, AuditLog)

    def list_by_user(self, user_id: str, limit: int = 100) -> list[AuditLog]:
        result = self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def list_all(self, limit: int = 100) -> list[AuditLog]:
        result = self.db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
