from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import ROLE_VIEWER, USER_STATUS_ACTIVE
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.database.repositories.identity_repository import UserRepository
from app.database.models.identity import User, UserSettings


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, username: str, email: str, password: str, role: str = ROLE_VIEWER) -> User:
        existing_user = self.users.get_by_username_or_email(username=username, email=email)
        if existing_user:
            raise ConflictError("Username or email already exists")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            status=USER_STATUS_ACTIVE,
        )
        self.users.add(user)
        self.users.flush()
        self.db.add(UserSettings(user_id=user.id))
        self.users.commit()
        self.users.refresh(user)
        return user

    def authenticate(self, username: str, password: str) -> User:
        user = self.users.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise NotFoundError("Invalid credentials")
        if user.status != USER_STATUS_ACTIVE:
            raise NotFoundError("User disabled")
        return user

    def issue_tokens(self, user: User) -> dict[str, str]:
        return {
            "access_token": create_access_token(user.id, {"role": user.role}),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }
