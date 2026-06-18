from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.identity import User, UserSettings
from app.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_username_or_email(self, username: str, email: str) -> User | None:
        result = self.db.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        return result.scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        result = self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    def get_active_by_id(self, user_id: str) -> User | None:
        result = self.db.execute(
            select(User).where((User.id == user_id) & (User.status == "ACTIVE"))
        )
        return result.scalar_one_or_none()


class UserSettingsRepository(BaseRepository[UserSettings]):
    def __init__(self, db: Session):
        super().__init__(db, UserSettings)

    def get_by_user_id(self, user_id: str) -> UserSettings | None:
        result = self.db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        return result.scalar_one_or_none()
