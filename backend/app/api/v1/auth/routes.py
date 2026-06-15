from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.core.exceptions import PermissionDeniedError
from app.core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_TRADER, ROLE_VIEWER
from app.database.models.identity import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    role = payload.role
    if role not in {ROLE_VIEWER, ROLE_TRADER, ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Invalid role")
    return auth_service.register(payload.username, payload.email, payload.password, role)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    user = auth_service.authenticate(payload.username, payload.password)
    return auth_service.issue_tokens(user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
