from __future__ import annotations

import logging
from typing import Any

from redis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

FLAG_TTL_SECONDS = {
    "paper_trading.enabled": 30,
    "live_trading.enabled": 10,
    "ai_agents.enabled": 30,
    "news_analysis.enabled": 60,
    "sentiment_analysis.enabled": 60,
    "experimental_features.enabled": 60,
}
DEFAULT_TTL = 60


def _key(*parts: str) -> str:
    return ":".join(["feature_flag", *parts])


class FeatureFlagCache:
    def __init__(self) -> None:
        self._client: Redis | None = None

    @property
    def client(self) -> Redis | None:
        if self._client is None:
            try:
                self._client = Redis.from_url(settings.redis_url, decode_responses=True)
                self._client.ping()
            except Exception as exc:
                logger.warning("feature flag cache unavailable: %s", exc)
                self._client = None
        return self._client

    def get(self, key: str) -> Any | None:
        try:
            value = self.client.get(_key("flag", key)) if self.client else None
            if value is None:
                return None
            import json
            return json.loads(value)
        except Exception as exc:
            logger.warning("feature flag cache get failed key=%s error=%s", key, exc)
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if self.client is None:
            return
        try:
            import json
            effective_ttl = ttl if ttl is not None else FLAG_TTL_SECONDS.get(key, DEFAULT_TTL)
            self.client.set(_key("flag", key), json.dumps(value), ex=effective_ttl)
        except Exception as exc:
            logger.warning("feature flag cache set failed key=%s error=%s", key, exc)

    def delete(self, key: str) -> None:
        if self.client is None:
            return
        try:
            self.client.delete(_key("flag", key))
        except Exception as exc:
            logger.warning("feature flag cache delete failed key=%s error=%s", key, exc)

    def delete_prefix(self, prefix: str) -> None:
        if self.client is None:
            return
        try:
            pattern = f"{_key(prefix)}:*"
            keys = list(self.client.scan_iter(pattern))
            if keys:
                self.client.delete(*keys)
        except Exception as exc:
            logger.warning("feature flag cache prefix delete failed prefix=%s error=%s", prefix, exc)

    def invalidate_all(self) -> None:
        if self.client is None:
            return
        try:
            pattern = _key("*")
            keys = list(self.client.scan_iter(pattern))
            if keys:
                self.client.delete(*keys)
        except Exception as exc:
            logger.warning("feature flag cache invalidate_all failed error=%s", exc)
