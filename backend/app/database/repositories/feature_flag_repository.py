from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models.feature_flag import FeatureFlag, FeatureFlagAssignment, FeatureFlagAuditLog
from app.database.repositories.base import BaseRepository


class FeatureFlagRepository(BaseRepository[FeatureFlag]):
    def __init__(self, db: Session):
        super().__init__(db, FeatureFlag)

    def get_by_key(self, key: str) -> FeatureFlag | None:
        return self.db.scalar(select(FeatureFlag).where(FeatureFlag.key == key))

    def list_flags(
        self,
        key: str | None = None,
        enabled: bool | None = None,
        environment: str | None = None,
        owner: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FeatureFlag]:
        statement = select(FeatureFlag).options(
            joinedload(FeatureFlag.assignments),
            joinedload(FeatureFlag.audit_logs),
        )
        if key is not None:
            statement = statement.where(FeatureFlag.key == key)
        if enabled is not None:
            statement = statement.where(FeatureFlag.enabled == enabled)
        if environment is not None:
            statement = statement.where(FeatureFlag.environment == environment)
        if owner is not None:
            statement = statement.where(FeatureFlag.owner == owner)
        statement = statement.order_by(FeatureFlag.key).limit(limit).offset(offset)
        return list(self.db.scalars(statement).all())

    def get_assignments(self, flag_id: str) -> list[FeatureFlagAssignment]:
        return list(
            self.db.scalars(
                select(FeatureFlagAssignment).where(FeatureFlagAssignment.flag_id == flag_id)
            ).all()
        )

    def delete_assignment(self, flag_id: str, assignment_id: str) -> FeatureFlagAssignment | None:
        assignment = self.db.scalar(
            select(FeatureFlagAssignment).where(
                (FeatureFlagAssignment.flag_id == flag_id)
                & (FeatureFlagAssignment.id == assignment_id)
            )
        )
        if assignment:
            self.db.delete(assignment)
        return assignment

    def get_audit_logs(self, flag_id: str, limit: int = 100) -> list[FeatureFlagAuditLog]:
        return list(
            self.db.scalars(
                select(FeatureFlagAuditLog)
                .where(FeatureFlagAuditLog.flag_id == flag_id)
                .order_by(FeatureFlagAuditLog.created_at.desc())
                .limit(limit)
            ).all()
        )

    def add_audit_log(
        self,
        flag_id: str,
        flag_key: str,
        action: str,
        actor_user_id: str | None = None,
        actor_role: str | None = None,
        ip_address: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        reason: str | None = None,
    ) -> FeatureFlagAuditLog:
        log = FeatureFlagAuditLog(
            flag_id=flag_id,
            flag_key=flag_key,
            action=action,
            old_value=old_value,
            new_value=new_value,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            ip_address=ip_address,
            reason=reason,
        )
        self.db.add(log)
        return log
