from __future__ import annotations


from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_current_user, get_feature_flag_service
from app.core.config import settings
from app.core.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.database.models.identity import User
from app.schemas.feature_flag import (
    AssignmentCreate,
    AssignmentRead,
    FeatureFlagAuditLogRead,
    FeatureFlagBootstrapResponse,
    FeatureFlagCreate,
    FeatureFlagEvaluateManyResponse,
    FeatureFlagEvaluateRequest,
    FeatureFlagEvaluateResponse,
    FeatureFlagRead,
    FeatureFlagUpdate,
)
from app.services.feature_flag_service import FeatureFlagService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return None


def _require_admin(current_user: User) -> None:
    if current_user.role not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        raise PermissionDeniedError("Permission denied")


def _require_super_admin(current_user: User) -> None:
    if current_user.role != ROLE_SUPER_ADMIN:
        raise PermissionDeniedError("Permission denied")


@router.post("/feature-flags/evaluate", response_model=FeatureFlagEvaluateManyResponse)
def evaluate_flags(
    payload: FeatureFlagEvaluateRequest,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    evaluated = [result.to_dict() for result in feature_flag_service.evaluate_many(payload.flags, user=current_user)]
    return {"flags": evaluated, "environment": settings.app_env, "user_id": current_user.id}


@router.get("/feature-flags/bootstrap", response_model=FeatureFlagBootstrapResponse)
def bootstrap_flags(
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    flags = feature_flag_service.get_admin_flags()
    evaluated = [feature_flag_service.evaluate(flag.key, user=current_user).to_dict() for flag in flags]
    return {"flags": evaluated, "environment": settings.app_env, "user_id": current_user.id}


@router.get("/feature-flags/{key}", response_model=FeatureFlagEvaluateResponse)
def evaluate_flag(
    key: str,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    return feature_flag_service.evaluate(key, user=current_user).to_dict()


@router.get("/admin/feature-flags", response_model=list[FeatureFlagRead])
def list_feature_flags(
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
    enabled: bool | None = None,
    environment: str | None = None,
    owner: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    _require_admin(current_user)
    return feature_flag_service.list_flags(enabled=enabled, environment=environment, owner=owner, limit=limit, offset=offset)


@router.get("/admin/feature-flags/{key}", response_model=FeatureFlagRead)
def get_feature_flag(
    key: str,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_admin(current_user)
    flag = feature_flag_service.repo.get_by_key(key)
    if not flag:
        raise NotFoundError(f"Feature flag '{key}' not found")
    return flag


@router.post("/admin/feature-flags", response_model=FeatureFlagRead, status_code=status.HTTP_201_CREATED)
def create_feature_flag(
    payload: FeatureFlagCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_super_admin(current_user)
    return feature_flag_service.create_flag(payload, actor=current_user, ip_address=_client_ip(request))


@router.put("/admin/feature-flags/{key}", response_model=FeatureFlagRead)
def update_feature_flag(
    key: str,
    payload: FeatureFlagUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_super_admin(current_user)
    return feature_flag_service.update_flag(key, payload, actor=current_user, ip_address=_client_ip(request))


@router.patch("/admin/feature-flags/{key}/enable", response_model=FeatureFlagRead)
def enable_feature_flag(
    key: str,
    request: Request,
    payload: dict | None = None,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_super_admin(current_user)
    reason = payload.get("reason") if isinstance(payload, dict) else None
    return feature_flag_service.enable_flag(key, actor=current_user, ip_address=_client_ip(request) if request else None, reason=reason)


@router.patch("/admin/feature-flags/{key}/disable", response_model=FeatureFlagRead)
def disable_feature_flag(
    key: str,
    request: Request,
    payload: dict | None = None,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_super_admin(current_user)
    reason = payload.get("reason") if isinstance(payload, dict) else None
    return feature_flag_service.disable_flag(key, actor=current_user, ip_address=_client_ip(request) if request else None, reason=reason)


@router.get("/admin/feature-flags/{key}/history", response_model=list[FeatureFlagAuditLogRead])
def feature_flag_history(
    key: str,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
    limit: int = 100,
):
    _require_admin(current_user)
    flag = feature_flag_service.repo.get_by_key(key)
    if not flag:
        raise NotFoundError(f"Feature flag '{key}' not found")
    return feature_flag_service.list_audit_logs(flag.id, limit=limit)


@router.post("/admin/feature-flags/{key}/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_feature_flag_assignment(
    key: str,
    payload: AssignmentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_super_admin(current_user)
    flag = feature_flag_service.repo.get_by_key(key)
    if not flag:
        raise NotFoundError(f"Feature flag '{key}' not found")
    return feature_flag_service.create_assignment(flag.id, payload, actor=current_user, ip_address=_client_ip(request))


@router.delete("/admin/feature-flags/{key}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature_flag_assignment(
    key: str,
    assignment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
):
    _require_super_admin(current_user)
    flag = feature_flag_service.repo.get_by_key(key)
    if not flag:
        raise NotFoundError(f"Feature flag '{key}' not found")
    feature_flag_service.delete_assignment(flag.id, assignment_id, actor=current_user, ip_address=_client_ip(request))
