from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_notification_service
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=list[NotificationRead])
def list_notifications(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    return notification_service.list(current_user.id)


@router.post("/", response_model=NotificationRead, status_code=201)
def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    user_id = payload.user_id or current_user.id
    if user_id != current_user.id and current_user.role not in {"ADMIN", "SUPER_ADMIN"}:
        raise PermissionDeniedError("Permission denied")
    return notification_service.create(user_id, payload.notification_type, payload.title, payload.message)



