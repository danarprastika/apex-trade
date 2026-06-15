from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.risk import ExposureRecord, RiskEvent, RiskProfile
from app.database.repositories.base import BaseRepository


class RiskProfileRepository(BaseRepository[RiskProfile]):
    def __init__(self, db: Session):
        super().__init__(db, RiskProfile)

    def get_by_user(self, user_id: str) -> RiskProfile | None:
        return self.db.scalar(select(RiskProfile).where(RiskProfile.user_id == user_id))


class RiskEventRepository(BaseRepository[RiskEvent]):
    def __init__(self, db: Session):
        super().__init__(db, RiskEvent)

    def list_by_user(self, user_id: str, limit: int = 100) -> list[RiskEvent]:
        return list(
            self.db.scalars(
                select(RiskEvent)
                .where(RiskEvent.user_id == user_id)
                .order_by(RiskEvent.created_at.desc())
                .limit(limit)
            ).all()
        )


class ExposureRecordRepository(BaseRepository[ExposureRecord]):
    def __init__(self, db: Session):
        super().__init__(db, ExposureRecord)
