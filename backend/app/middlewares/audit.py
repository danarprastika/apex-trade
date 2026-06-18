from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import app.database.session as session_module
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    skip_paths = {"/", "/api/v1/health", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in self.skip_paths:
            return await call_next(request)

        response = await call_next(request)
        self._audit_request(request, response)
        return response

    def _audit_request(self, request: Request, response: Response) -> None:
        if not self._should_audit():
            return

        SessionLocal = session_module.SessionLocal
        db = SessionLocal()
        try:
            audit = AuditService(db)
            audit.log(
                entity_type="HTTP",
                entity_id=f"{request.method} {request.url.path}",
                action=f"HTTP_{request.method}_{response.status_code}",
                user_id=self._get_user_id(request),
                old_value=self._extract_request_payload(request),
                new_value={"status_code": response.status_code},
                ip_address=self._get_client_ip(request),
            )
        except Exception:
            logger.exception("audit log write failed path=%s method=%s", request.url.path, request.method)
        finally:
            db.close()

    @staticmethod
    def _should_audit() -> bool:
        return True

    @staticmethod
    def _get_user_id(request: Request) -> str | None:
        user = getattr(request.state, "current_user", None)
        return getattr(user, "id", None)

    @staticmethod
    def _get_client_ip(request: Request) -> str | None:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
        if request.client:
            return request.client.host
        return None

    @staticmethod
    def _extract_request_payload(request: Request) -> dict[str, Any] | None:
        body = getattr(request.state, "body", None)
        if body is None:
            return None
        try:
            return json.loads(body.decode() if isinstance(body, bytes) else body)
        except (TypeError, ValueError):
            return {"body": "<non-json>"}
