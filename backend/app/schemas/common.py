from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool = True
    message: str = "Request successful"
    data: dict | list | None = None


class APIError(BaseModel):
    success: bool = False
    message: str
    errors: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str = "unknown"
    redis: str = "unknown"
