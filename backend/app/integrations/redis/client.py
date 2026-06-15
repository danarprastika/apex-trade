import redis

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self.client.ping())
