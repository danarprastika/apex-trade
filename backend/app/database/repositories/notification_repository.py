from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.notification import Notification
from app.database.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session):
        super().__init__(db, Notification)

    def list_by_user(self, user_id: str, limit: int = 100) -> list[Notification]:
        result = self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
