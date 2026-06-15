from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import ROLE_VIEWER


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = ROLE_VIEWER

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed_roles = {"VIEWER", "TRADER", "ADMIN", "SUPER_ADMIN"}
        if value not in allowed_roles:
            raise ValueError("role must be one of VIEWER, TRADER, ADMIN, SUPER_ADMIN")
        return value


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: str
    username: str
    email: str
    role: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UserSettingsRead(BaseModel):
    id: str
    user_id: str
    timezone: str
    language: str
    theme: str
    telegram_chat_id: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    timezone: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=20)
    theme: str | None = Field(default=None, max_length=20)
    telegram_chat_id: str | None = Field(default=None, max_length=100)

