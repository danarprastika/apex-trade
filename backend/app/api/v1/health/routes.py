from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_health_service
from app.integrations.redis.client import RedisClient
from app.services.health_service import HealthService

router = APIRouter()


_http_requests_total: dict[str, int] = {}
_http_request_duration_seconds: dict[str, float] = {}
_database_connections_active = 0
_redis_connected = 0
_event_bus_published_total: dict[str, int] = {}
_risk_veto_total: dict[str, int] = {}
_paper_orders_total: dict[str, int] = {}


def _incr_counter(store: dict[str, int], key: str) -> None:
    store[key] = store.get(key, 0) + 1


def _set_gauge(value: int) -> None:
    return value


@router.get("/health")
def health(
    check_dependencies: bool = False,
    health_service: HealthService = Depends(get_health_service),
):
    return health_service.get_health(check_dependencies=check_dependencies)


def _update_connection_gauges() -> None:
    global _database_connections_active, _redis_connected
    try:
        from app.database.session import engine as db_engine
        _database_connections_active = int(getattr(getattr(db_engine, "pool", None), "size", lambda: 0)())
    except Exception:
        _database_connections_active = 0

    try:
        redis_client = RedisClient()
        _redis_connected = 1 if redis_client.ping() else 0
    except Exception:
        _redis_connected = 0


def _render_metric(name: str, documentation: str, metric_type: str, value: Any, labels: dict[str, str] | None = None) -> str:
    label_str = ""
    if labels:
        label_str = "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}"
    return f"# HELP {name} {documentation}\n# TYPE {name} {metric_type}\n{name}{label_str} {value}\n"


@router.get("/metrics")
def metrics() -> Response:
    _update_connection_gauges()
    output_lines = []
    for (method, endpoint, status), value in _http_requests_total.items():
        output_lines.append(_render_metric("apex_http_requests_total", "Total HTTP requests", "counter", value, {"method": method, "endpoint": endpoint, "status": status}))
    for (method, endpoint), value in _http_request_duration_seconds.items():
        output_lines.append(_render_metric("apex_http_request_duration_seconds", "HTTP request duration in seconds", "gauge", value, {"method": method, "endpoint": endpoint}))
    output_lines.append(_render_metric("apex_database_connections_active", "Active database connections", "gauge", _database_connections_active))
    output_lines.append(_render_metric("apex_redis_connected", "Redis connection status", "gauge", _redis_connected))
    for event_type, value in _event_bus_published_total.items():
        output_lines.append(_render_metric("apex_event_bus_published_total", "Total events published to event bus", "counter", value, {"event_type": event_type}))
    for reason, value in _risk_veto_total.items():
        output_lines.append(_render_metric("apex_risk_veto_total", "Total risk vetoes", "counter", value, {"reason": reason}))
    for key, value in _paper_orders_total.items():
        side, status = key.split("|", 1)
        output_lines.append(_render_metric("apex_paper_orders_total", "Total paper orders", "counter", value, {"side": side, "status": status}))
    return Response(content="\n".join(output_lines), media_type="text/plain; version=0.0.4")
