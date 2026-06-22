"""Redis configuration."""

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from src.infrastructure.config.settings import settings

pool = ConnectionPool.from_url(
    settings.redis_url,
    max_connections=10,
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:
    """Get Redis client."""
    return redis.Redis(connection_pool=pool)
