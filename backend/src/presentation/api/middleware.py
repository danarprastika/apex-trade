"""FastAPI middleware."""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.application.exceptions import ApplicationException


async def application_exception_middleware(request: Request, call_next):
    """Handle application exceptions."""
    try:
        return await call_next(request)
    except ApplicationException as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": exc.code, "message": exc.message}},
        )


middleware = [application_exception_middleware]
