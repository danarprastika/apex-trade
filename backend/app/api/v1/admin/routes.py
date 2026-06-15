from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_audit_service, get_current_user, get_db
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.core.exceptions import PermissionDeniedError
from app.database.models.identity import User
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/users", response_model=list[dict])
def admin_users(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {ROLE_SUPER_ADMIN, ROLE_ADMIN}:
        raise PermissionDeniedError("Permission denied")
    return db.query(User).all()


@router.get("/system", response_model=dict)
def system_status(current_user: User = Depends(get_current_user)):
    if current_user.role != ROLE_SUPER_ADMIN:
        raise PermissionDeniedError("Permission denied")
    return {"status": "ok", "mode": "admin"}


@router.get("/audit", response_model=list[AuditLogRead])
def audit_logs(
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    if current_user.role != ROLE_SUPER_ADMIN:
        raise PermissionDeniedError("Permission denied")
    return audit_service.list_all()



