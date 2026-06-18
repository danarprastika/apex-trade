from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.database.models.identity import User


class RBACMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {"/health", "/auth", "/auth/login", "/auth/register", "/auth/refresh", "/auth/forgot-password", "/auth/reset-password"}

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
        if self._is_public_path(request.url.path):
            return await call_next(request)

        user = getattr(request.state, "current_user", None)
        if not user:
            return await call_next(request)

        required_roles = self._get_required_roles(request.url.path)
        if required_roles and user.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        for public in self.PUBLIC_PATHS:
            if path == public or path.startswith(public + "/"):
                return True
        return False

    def _get_required_roles(self, path: str) -> set[str] | None:
        if path.startswith("/admin"):
            return {"SUPER_ADMIN"}
        if path.startswith("/trading") or path.startswith("/portfolio") or path.startswith("/risk"):
            return {"ADMIN", "TRADER"}
        if path.startswith("/market") or path.startswith("/exchanges"):
            return {"VIEWER"}
        return None


def require_roles(*roles: str):
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            request: Request | None = kwargs.get("request")
            if not request:
                request = next((a for a in args if isinstance(a, Request)), None)
            if request:
                user: User | None = getattr(request.state, "current_user", None)
                if user and user.role not in roles:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator