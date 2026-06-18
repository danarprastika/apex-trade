import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base


def get_test_db_url():
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def integration_db_session():
    db_url = get_test_db_url()
    engine = create_engine(db_url)
    if "sqlite" in db_url:
        Base.metadata.create_all(engine)
    else:
        Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        if "sqlite" in db_url:
            Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def integration_redis_client():
    redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
    try:
        import redis
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        yield client
        client.flushdb()
    except Exception:
        import time
        class MockRedis:
            def __init__(self):
                self._store: dict[str, tuple[Any, float | None]] = {}
            def ping(self):
                return True
            def flushdb(self):
                self._store.clear()
            def set(self, key, value, ex=None):
                expire_at = time.time() + ex if ex else None
                self._store[key] = (value, expire_at)
                return True
            def get(self, key):
                value, expire_at = self._store.get(key, (None, None))
                if expire_at is not None and time.time() >= expire_at:
                    self._store.pop(key, None)
                    return None
                return value
            def delete(self, key):
                return self._store.pop(key, None) is not None
            def expire(self, key, ttl):
                if key in self._store:
                    value, _ = self._store[key]
                    self._store[key] = (value, time.time() + ttl)
                    return True
                return False
        yield MockRedis()


@pytest.fixture
def cleanup_tables():
    yield
