from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_audit_service, get_current_user
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/users", response_model=list[dict])
async def admin_users(
    current_user: Annotated[User, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return await audit_service.list_all()


@router.get("/system", response_model=dict)
async def system_status(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != ROLE_SUPER_ADMIN:
        raise PermissionDeniedError("Permission denied")
    return {"status": "ok", "mode": "admin"}


@router.get("/audit", response_model=list[AuditLogRead])
async def audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
):
    if current_user.role != ROLE_SUPER_ADMIN:
        raise PermissionDeniedError("Permission denied")
    return await audit_service.list_all()
