from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_user_service
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.auth import UserRead, UserSettingsRead, UserSettingsUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=list[UserRead])
def list_users(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return user_service.list_users()


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/profile")
def read_my_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.get_or_create_profile(current_user)


@router.get("/me/settings", response_model=UserSettingsRead)
def read_my_settings(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.get_or_create_profile(current_user)


@router.patch("/me/settings", response_model=UserSettingsRead)
def update_my_settings(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    updates = payload.model_dump(exclude_unset=True)
    return user_service.update_settings(current_user, **updates)


@router.post("/me/settings/telegram", response_model=UserSettingsRead)
def link_telegram(
    payload: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    if payload.telegram_chat_id is None:
        raise PermissionDeniedError("telegram_chat_id is required")
    return user_service.update_settings(current_user, telegram_chat_id=payload.telegram_chat_id)


@router.delete("/me/settings/telegram", response_model=UserSettingsRead)
def unlink_telegram(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_settings(current_user, telegram_chat_id=None)



