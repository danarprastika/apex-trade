from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.risk import ExposureRecord, RiskEvent, RiskProfile
from app.database.repositories.base import BaseRepository


class RiskProfileRepository(BaseRepository[RiskProfile]):
    def __init__(self, db: Session):
        super().__init__(db, RiskProfile)

    def get_by_user(self, user_id: str) -> RiskProfile | None:
        result = self.db.execute(select(RiskProfile).where(RiskProfile.user_id == user_id))
        return result.scalar_one_or_none()


class RiskEventRepository(BaseRepository[RiskEvent]):
    def __init__(self, db: Session):
        super().__init__(db, RiskEvent)

    def list_by_user(self, user_id: str, limit: int = 100) -> list[RiskEvent]:
        result = self.db.execute(
            select(RiskEvent)
            .where(RiskEvent.user_id == user_id)
            .order_by(RiskEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ExposureRecordRepository(BaseRepository[ExposureRecord]):
    def __init__(self, db: Session):
        super().__init__(db, ExposureRecord)

    def get_by_user_and_asset(self, user_id: str, asset_id: str) -> ExposureRecord | None:
        result = self.db.execute(
            select(ExposureRecord).where(
                (ExposureRecord.user_id == user_id) & (ExposureRecord.asset_id == asset_id)
            )
        )
        return result.scalar_one_or_none()
