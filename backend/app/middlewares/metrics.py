from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from prometheus_client import Counter, Gauge
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

apex_http_requests_total = Counter(
    "apex_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

apex_http_request_duration_seconds = Gauge(
    "apex_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        endpoint = request.url.path
        method = request.method
        status = str(response.status_code)
        apex_http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        apex_http_request_duration_seconds.labels(method=method, endpoint=endpoint).set(duration)
        return response
