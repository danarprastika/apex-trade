from __future__ import annotations

from app.integrations.redis.client import RedisClient


class TokenBlacklistService:
    def __init__(self, redis_client: RedisClient | None = None):
        self.redis = redis_client or RedisClient()

    def revoke(self, token_id: str, ttl_seconds: int) -> None:
        key = f"blacklist:{token_id}"
        self.redis.client.setex(key, ttl_seconds, "1")

    def is_revoked(self, token_id: str) -> bool:
        key = f"blacklist:{token_id}"
        try:
            return self.redis.client.exists(key) == 1
        except Exception:
            return False


token_blacklist = TokenBlacklistService()