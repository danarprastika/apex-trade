import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base


@pytest.fixture
def e2e_client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def e2e_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def authenticated_user(e2e_client, e2e_db_session):
    import app.api.deps as deps
    import app.database.session as session_module

    original_deps = deps.SessionLocal
    original_session = session_module.SessionLocal
    deps.SessionLocal = e2e_db_session
    session_module.SessionLocal = e2e_db_session

    try:
        from app.schemas.auth import UserCreate

        user_data = UserCreate(
            username="e2euser",
            email="e2e@example.com",
            password="testpassword123",
        )
        e2e_client.post("/api/v1/auth/register", json=user_data.model_dump())
    finally:
        deps.SessionLocal = original_deps
        session_module.SessionLocal = original_session

    return {"username": user_data.username, "password": user_data.password}


@pytest.fixture
def auth_tokens(e2e_client, authenticated_user):
    response = e2e_client.post(
        "/api/v1/auth/login",
        json={
            "username": authenticated_user["username"],
            "password": authenticated_user["password"],
        },
    )
    return {
        "access_token": response.json()["access_token"],
        "refresh_token": response.json()["refresh_token"],
    }
