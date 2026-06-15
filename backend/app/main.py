from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import PermissionDeniedError, ValidationError
from app.core.logging import configure_logging
from app.database.base import Base
from app.database.session import engine
from app.middlewares.audit import AuditLogMiddleware
from app.middlewares.request_body import RequestBodyMiddleware

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.debug and settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
        logger.info("database tables created on startup")
    logger.info("apex backend started", env=settings.app_env)
    try:
        yield
    finally:
        engine.dispose()
        logger.info("apex backend stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="APEX enterprise AI-powered multi-asset trading platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditLogMiddleware)
app.add_middleware(RequestBodyMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("request validation failed", errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Request validation failed", "errors": exc.errors()},
    )


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(_: Request, exc: PermissionDeniedError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(ValidationError)
async def app_validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("database error")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Database error"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled exception")
    detail: Any = "Internal server error" if not settings.debug else str(exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": detail},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running"}
