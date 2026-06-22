"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import settings
from src.presentation.api.dependencies import get_settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}


@app.get("/health/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    return {"ready": True}


@app.get("/health/live")
async def liveness_check() -> dict:
    """Liveness check endpoint."""
    return {"alive": True}


# API v1 router placeholder
from src.presentation.api.v1.router import router as api_v1_router

app.include_router(api_v1_router, prefix=settings.api_prefix)
