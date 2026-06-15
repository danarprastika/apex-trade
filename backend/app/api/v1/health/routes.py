from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_health_service
from app.schemas.common import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(
    check_dependencies: bool = Query(False),
    health_service: HealthService = Depends(get_health_service),
):
    return health_service.get_health(check_dependencies=check_dependencies)


@router.get("/metrics")
def metrics(health_service: HealthService = Depends(get_health_service)):
    health = health_service.get_health(check_dependencies=True)
    return {
        "status": health["status"],
        "database": health["database"],
        "redis": health["redis"],
    }
