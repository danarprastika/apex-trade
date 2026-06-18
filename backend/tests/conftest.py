import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.events.bus import EventBus


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def redis_client():
    mock_redis = type("MockRedis", (), {"ping": lambda self: True, "flushdb": lambda self: None})()
    mock_client = type("MockRedisClient", (), {"client": mock_redis})()
    yield mock_client


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    from app.database.models.identity import User
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="TRADER",
        status="ACTIVE"
    )
    db_session.add(user)
    db_session.flush()
    return user
