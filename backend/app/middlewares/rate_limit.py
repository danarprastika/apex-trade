from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.integrations.redis.client import RedisClient


class RateLimitMiddleware(BaseHTTPMiddleware):
    RATE_LIMIT_IP = 100
    RATE_LIMIT_USER = 200
    WINDOW_SECONDS = 60
    SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app: ASGIApp, redis_client: RedisClient | None = None):
        super().__init__(app)
        self.redis = redis_client or RedisClient()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = request.url.path.rstrip("/") or "/"
        if path in self.SKIP_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        limit = self.RATE_LIMIT_USER if user_id else self.RATE_LIMIT_IP
        key_base = f"rate_limit:{user_id}" if user_id else f"rate_limit:ip:{client_ip}"
        key = f"{key_base}:{self._get_window_key()}"

        try:
            current = self.redis.client.incr(key)
            if current == 1:
                self.redis.client.expire(key, self.WINDOW_SECONDS)
            if current > limit:
                retry_after = self._get_retry_after()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests",
                    headers={"Retry-After": str(retry_after)},
                )
        except HTTPException:
            raise
        except Exception:
            pass

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    @staticmethod
    def _get_user_id(request: Request) -> str | None:
        user = getattr(request.state, "current_user", None)
        return getattr(user, "id", None) if user else None

    @staticmethod
    def _get_window_key() -> int:
        from time import time
        return int(time() // 60)

    @staticmethod
    def _get_retry_after() -> int:
        from time import time
        remaining = 60 - int(time()) % 60
        return max(1, remaining)