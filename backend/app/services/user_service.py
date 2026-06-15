from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models.identity import User, UserSettings
from app.database.repositories.identity_repository import UserRepository, UserSettingsRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.settings = UserSettingsRepository(db)

    def get_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        return self.users.list(limit=limit, offset=offset)

    def get_or_create_profile(self, user: User) -> UserSettings:
        profile = self.settings.get_by_user_id(user.id)
        if profile:
            return profile
        profile = UserSettings(user_id=user.id)
        self.settings.add(profile)
        self.settings.commit()
        self.settings.refresh(profile)
        return profile

    def update_settings(self, user: User, **kwargs) -> UserSettings:
        profile = self.get_or_create_profile(user)
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        self.settings.commit()
        self.settings.refresh(profile)
        return profile

