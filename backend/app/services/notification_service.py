from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models.notification import Notification
from app.database.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationRepository(db)

    def create(self, user_id: str, notification_type: str, title: str, message: str) -> Notification:
        notification = self.notifications.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )
        self.notifications.commit()
        self.notifications.refresh(notification)
        logger.info("Created notification notification_id=%s user_id=%s", notification.id, user_id)
        return notification

    def list(self, user_id: str, limit: int = 100) -> list[Notification]:
        return self.notifications.list_by_user(user_id, limit=limit)

    def mark_sent(self, notification_id: str) -> Notification:
        notification = self.notifications.get(notification_id)
        if not notification:
            raise NotFoundError("Notification not found")
        notification.status = "SENT"
        notification.sent_at = datetime.now(timezone.utc)
        self.notifications.commit()
        self.notifications.refresh(notification)
        return notification
