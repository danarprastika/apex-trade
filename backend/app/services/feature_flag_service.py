from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import ROLE_SUPER_ADMIN
from app.core.exceptions import ConflictError, FeatureDisabledError, NotFoundError, PermissionDeniedError, ValidationError
from app.database.models.feature_flag import FeatureFlag, FeatureFlagAssignment, FeatureFlagAuditLog
from app.database.models.identity import User
from app.database.repositories.feature_flag_repository import FeatureFlagRepository
from app.integrations.feature_flag.cache import FeatureFlagCache

logger = logging.getLogger(__name__)


class FeatureFlagEvaluationResult:
    def __init__(
        self,
        flag: FeatureFlag,
        enabled: bool,
        reason: str,
        environment: str,
        variant: dict | None = None,
        rollout_bucket: int | None = None,
        user_context: dict | None = None,
        dependencies_evaluated: list[str] | None = None,
    ):
        self.flag = flag
        self.enabled = enabled
        self.reason = reason
        self.environment = environment
        self.variant = variant
        self.rollout_bucket = rollout_bucket
        self.user_context = user_context
        self.dependencies_evaluated = dependencies_evaluated or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "flag_key": self.flag.key,
            "enabled": self.enabled,
            "reason": self.reason,
            "environment": self.environment,
            "variant": self.variant,
            "rollout_bucket": self.rollout_bucket,
            "user_context": self.user_context,
            "dependencies_evaluated": self.dependencies_evaluated,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }


class FeatureFlagService:
    def __init__(self, db: Session, audit_service: Any | None = None):
        self.db = db
        self.repo = FeatureFlagRepository(db)
        self.cache = FeatureFlagCache()
        self.audit_service = audit_service

    def is_enabled(self, key: str, user: User | None = None, environment: str | None = None) -> bool:
        result = self.evaluate(key, user=user, environment=environment)
        return result.enabled

    def evaluate(
        self,
        key: str,
        user: User | None = None,
        environment: str | None = None,
    ) -> FeatureFlagEvaluationResult:
        env = environment or settings.app_env

        cached = self.cache.get(key)
        if cached is not None and cached.get("environment") == env:
            cached_flag = FeatureFlag(**cached.get("flag", {}))
            return FeatureFlagEvaluationResult(
                flag=cached_flag,
                enabled=cached.get("enabled", False),
                reason="cached",
                environment=env,
            )

        flag = self.repo.get_by_key(key)
        if not flag:
            logger.warning("feature flag not found key=%s", key)
            return FeatureFlagEvaluationResult(
                flag=_missing_flag(key),
                enabled=False,
                reason="flag_not_found",
                environment=env,
            )

        if flag.environment != env and flag.environment != "all":
            return FeatureFlagEvaluationResult(
                flag=flag,
                enabled=False,
                reason="environment_mismatch",
                environment=env,
            )

        if not flag.enabled:
            reason = "kill_switch_disabled" if flag.is_kill_switch else "globally_disabled"
            return FeatureFlagEvaluationResult(
                flag=flag,
                enabled=False,
                reason=reason,
                environment=env,
            )

        if user:
            user_ctx = {"user_id": user.id, "role": user.role}
            user_enabled, user_reason = self._evaluate_user_assignments(flag, user, env)
            if user_enabled:
                result = FeatureFlagEvaluationResult(
                    flag=flag,
                    enabled=True,
                    reason=user_reason,
                    environment=env,
                    user_context=user_ctx,
                )
                self.cache.set(key, _serialize_for_cache(result))
                return result

        global_enabled, global_reason = self._evaluate_global_assignments(flag, env)
        if global_enabled:
            result = FeatureFlagEvaluationResult(
                flag=flag,
                enabled=True,
                reason=global_reason,
                environment=env,
            )
            self.cache.set(key, _serialize_for_cache(result))
            return result

        return FeatureFlagEvaluationResult(
            flag=flag,
            enabled=False,
            reason="no_matching_assignment",
            environment=env,
        )

    def evaluate_many(
        self,
        keys: list[str],
        user: User | None = None,
        environment: str | None = None,
    ) -> list[FeatureFlagEvaluationResult]:
        return [self.evaluate(key, user=user, environment=environment) for key in keys]

    def require_enabled(self, key: str, user: User | None = None, environment: str | None = None) -> FeatureFlagEvaluationResult:
        try:
            result = self.evaluate(key, user=user, environment=environment)
        except Exception as exc:
            logger.exception("feature flag evaluation failed key=%s", key)
            raise FeatureDisabledError(f"Feature '{key}' is unavailable: {exc}") from exc
        if not result.enabled:
            raise FeatureDisabledError(f"Feature '{key}' is disabled: {result.reason}")
        return result

    def get_admin_flags(self, environment: str | None = None) -> list[FeatureFlag]:
        return self.repo.list_flags(environment=environment)

    def list_flags(
        self,
        key: str | None = None,
        enabled: bool | None = None,
        environment: str | None = None,
        owner: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FeatureFlag]:
        return self.repo.list_flags(key=key, enabled=enabled, environment=environment, owner=owner, limit=limit, offset=offset)

    def create_flag(self, payload: Any, actor: User, ip_address: str | None = None) -> FeatureFlag:
        if self.repo.get_by_key(payload.key):
            raise ConflictError(f"Feature flag '{payload.key}' already exists")

        flag = FeatureFlag(
            key=payload.key,
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            environment=payload.environment,
            owner=payload.owner,
            flag_metadata=payload.metadata,
            is_kill_switch=payload.is_kill_switch,
            failure_mode=payload.failure_mode,
        )
        self.repo.add(flag)
        self.repo.commit()
        self.repo.refresh(flag)

        self._log_feature_flag_audit(
            flag=flag,
            action="create",
            actor=actor,
            old_value=None,
            new_value=_flag_snapshot(flag),
            ip_address=ip_address,
            reason=payload.reason,
        )
        self.cache.invalidate_all()
        logger.info("created feature flag key=%s enabled=%s actor=%s", flag.key, flag.enabled, actor.id)
        return flag

    def update_flag(
        self,
        key: str,
        payload: Any,
        actor: User,
        ip_address: str | None = None,
    ) -> FeatureFlag:
        flag = self.repo.get_by_key(key)
        if not flag:
            raise NotFoundError(f"Feature flag '{key}' not found")

        old_value = _flag_snapshot(flag)

        if payload.name is not None:
            flag.name = payload.name
        if payload.description is not None:
            flag.description = payload.description
        if payload.enabled is not None:
            flag.enabled = payload.enabled
        if payload.environment is not None:
            flag.environment = payload.environment
        if payload.owner is not None:
            flag.owner = payload.owner
        if payload.metadata is not None:
            flag.flag_metadata = payload.metadata
        if payload.is_kill_switch is not None:
            flag.is_kill_switch = payload.is_kill_switch
        if payload.failure_mode is not None:
            flag.failure_mode = payload.failure_mode

        self.repo.commit()
        self.repo.refresh(flag)

        self._log_feature_flag_audit(
            flag=flag,
            action="update",
            actor=actor,
            old_value=old_value,
            new_value=_flag_snapshot(flag),
            ip_address=ip_address,
            reason=payload.reason,
        )
        self.cache.invalidate_all()
        logger.info("updated feature flag key=%s enabled=%s actor=%s", key, flag.enabled, actor.id)
        return flag

    def enable_flag(self, key: str, actor: User, ip_address: str | None = None, reason: str | None = None) -> FeatureFlag:
        flag = self.repo.get_by_key(key)
        if not flag:
            raise NotFoundError(f"Feature flag '{key}' not found")
        if key == "live_trading.enabled" and actor.role != ROLE_SUPER_ADMIN:
            raise PermissionDeniedError("Only SUPER_ADMIN can enable live trading")

        old_value = _flag_snapshot(flag)
        flag.enabled = True
        self.repo.commit()
        self.repo.refresh(flag)

        self._log_feature_flag_audit(
            flag=flag,
            action="enable",
            actor=actor,
            old_value=old_value,
            new_value=_flag_snapshot(flag),
            ip_address=ip_address,
            reason=reason,
        )
        self.cache.delete(key)
        logger.info("enabled feature flag key=%s actor=%s reason=%s", key, actor.id, reason)
        return flag

    def disable_flag(
        self,
        key: str,
        actor: User,
        ip_address: str | None = None,
        reason: str | None = None,
    ) -> FeatureFlag:
        flag = self.repo.get_by_key(key)
        if not flag:
            raise NotFoundError(f"Feature flag '{key}' not found")

        old_value = _flag_snapshot(flag)
        flag.enabled = False
        self.repo.commit()
        self.repo.refresh(flag)

        self._log_feature_flag_audit(
            flag=flag,
            action="disable",
            actor=actor,
            old_value=old_value,
            new_value=_flag_snapshot(flag),
            ip_address=ip_address,
            reason=reason,
        )
        self.cache.delete(key)
        logger.info("disabled feature flag key=%s actor=%s reason=%s", key, actor.id, reason)
        return flag

    def create_assignment(self, flag_id: str, payload: Any, actor: User, ip_address: str | None = None) -> FeatureFlagAssignment:
        flag = self.repo.get(flag_id)
        if not flag:
            raise NotFoundError("Feature flag not found")

        target_type = payload.target_type.value
        if target_type == "user" and not payload.target_id:
            raise ValidationError("target_id is required for user assignments")
        if target_type == "role" and not payload.target_role:
            raise ValidationError("target_role is required for role assignments")
        if target_type == "segment" and not payload.target_id:
            raise ValidationError("target_id is required for segment assignments")

        assignment = FeatureFlagAssignment(
            flag_id=flag_id,
            target_type=target_type,
            target_id=payload.target_id,
            target_role=payload.target_role,
            rollout_percentage=payload.rollout_percentage,
            environment=payload.environment,
            enabled=payload.enabled,
            flag_metadata=payload.metadata,
        )
        self.repo.add(assignment)
        self.repo.commit()
        self.repo.refresh(assignment)

        self._log_feature_flag_audit(
            flag=flag,
            action="assignment_create",
            actor=actor,
            old_value=None,
            new_value={
                "assignment_id": assignment.id,
                "target_type": target_type,
                "target_id": payload.target_id,
                "target_role": payload.target_role,
                "rollout_percentage": float(payload.rollout_percentage) if payload.rollout_percentage is not None else None,
                "environment": payload.environment,
                "enabled": payload.enabled,
            },
            ip_address=ip_address,
        )
        self.cache.invalidate_all()
        return assignment

    def delete_assignment(self, flag_id: str, assignment_id: str, actor: User, ip_address: str | None = None) -> FeatureFlagAssignment:
        flag = self.repo.get(flag_id)
        if not flag:
            raise NotFoundError("Feature flag not found")

        assignment = self.repo.delete_assignment(flag_id, assignment_id)
        if not assignment:
            raise NotFoundError("Feature flag assignment not found")

        self.repo.commit()
        self._log_feature_flag_audit(
            flag=flag,
            action="assignment_delete",
            actor=actor,
            old_value={
                "assignment_id": assignment.id,
                "target_type": assignment.target_type,
                "target_id": assignment.target_id,
                "target_role": assignment.target_role,
                "rollout_percentage": float(assignment.rollout_percentage) if assignment.rollout_percentage is not None else None,
                "environment": assignment.environment,
                "enabled": assignment.enabled,
            },
            new_value=None,
            ip_address=ip_address,
        )
        self.cache.invalidate_all()
        return assignment

    def _evaluate_user_assignments(self, flag: FeatureFlag, user: User, environment: str) -> tuple[bool, str]:
        assignments = [a for a in flag.assignments if a.enabled]
        for assignment in assignments:
            if assignment.target_type == "user" and assignment.target_id == user.id:
                if assignment.environment and assignment.environment != environment:
                    continue
                if assignment.rollout_percentage is not None:
                    bucket = _rollout_bucket(user.id, flag.key)
                    if bucket >= assignment.rollout_percentage:
                        continue
                return True, "user_assignment"
            if assignment.target_type == "role" and assignment.target_role == user.role:
                if assignment.environment and assignment.environment != environment:
                    continue
                if assignment.rollout_percentage is not None:
                    bucket = _rollout_bucket(user.id, flag.key)
                    if bucket >= assignment.rollout_percentage:
                        continue
                return True, "role_assignment"
        return False, "no_user_assignment"

    def _evaluate_global_assignments(self, flag: FeatureFlag, environment: str) -> tuple[bool, str]:
        assignments = [a for a in flag.assignments if a.enabled]
        if not assignments:
            return True, "global_enabled"
        for assignment in assignments:
            if assignment.target_type not in {"user", "role"}:
                if assignment.environment and assignment.environment != environment:
                    continue
                if assignment.rollout_percentage is not None:
                    bucket = _rollout_bucket("global", flag.key)
                    if bucket >= assignment.rollout_percentage:
                        continue
                return True, "global_assignment"
        return False, "no_global_assignment"

    def _log_feature_flag_audit(
        self,
        flag: FeatureFlag,
        action: str,
        actor: User,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
        ip_address: str | None = None,
        reason: str | None = None,
    ) -> FeatureFlagAuditLog:
        log = self.repo.add_audit_log(
            flag_id=flag.id,
            flag_key=flag.key,
            action=action,
            actor_user_id=actor.id,
            actor_role=actor.role,
            ip_address=ip_address,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
        )
        self.repo.commit()
        return log

    def list_audit_logs(self, flag_id: str, limit: int = 100) -> list[FeatureFlagAuditLog]:
        return self.repo.get_audit_logs(flag_id, limit=limit)


def _flag_snapshot(flag: FeatureFlag) -> dict[str, Any]:
    return {
        "id": flag.id,
        "key": flag.key,
        "name": flag.name,
        "enabled": flag.enabled,
        "environment": flag.environment,
        "owner": flag.owner,
        "metadata": flag.flag_metadata,
        "is_kill_switch": flag.is_kill_switch,
        "failure_mode": flag.failure_mode,
    }


def _missing_flag(key: str) -> FeatureFlag:
    return FeatureFlag(key=key, name=key, enabled=False, environment="development", is_kill_switch=False, failure_mode="fail_closed")


def _serialize_for_cache(result: FeatureFlagEvaluationResult) -> dict[str, Any]:
    return {
        "flag": {
            "id": result.flag.id,
            "key": result.flag.key,
            "name": result.flag.name,
            "enabled": result.flag.enabled,
            "environment": result.flag.environment,
            "is_kill_switch": result.flag.is_kill_switch,
            "failure_mode": result.flag.failure_mode,
        },
        "enabled": result.enabled,
        "environment": result.environment,
    }


def _rollout_bucket(user_id: str, flag_key: str) -> int:
    raw = hashlib.sha256(f"{user_id}:{flag_key}".encode()).hexdigest()
    return int(raw[:8], 16) % 100
