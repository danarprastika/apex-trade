from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import engine
from app.integrations.redis.client import RedisClient

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self) -> None:
        self.redis = RedisClient()

    def check_database(self) -> dict[str, str]:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"status": "ok"}
        except SQLAlchemyError as exc:
            logger.exception("Database health check failed")
            return {"status": "error", "error": str(exc)}

    def check_redis(self) -> dict[str, str]:
        try:
            if self.redis.ping():
                return {"status": "ok"}
        except Exception as exc:
            logger.exception("Redis health check failed")
            return {"status": "error", "error": str(exc)}
        return {"status": "error", "error": "redis ping failed"}

    def get_health(self, check_dependencies: bool = False) -> dict[str, str | dict[str, str]]:
        if not check_dependencies:
            return {
                "status": "healthy",
                "service": "backend",
                "database": "not_checked",
                "redis": "not_checked",
            }

        database = self.check_database()
        redis = self.check_redis()
        status = "healthy" if database["status"] == "ok" and redis["status"] == "ok" else "degraded"
        return {
            "status": status,
            "service": "backend",
            "database": database["status"],
            "redis": redis["status"],
        }
