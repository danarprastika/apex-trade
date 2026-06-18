from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database.models
import app.database.session as session_module
from app.database.base import Base
from app.database.models.audit import AuditLog
from app.main import app


def test_audit_middleware_logs_failed_endpoint_requests(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    AuditLog.__table__.create(engine, checkfirst=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr(session_module, "SessionLocal", SessionLocal)

    from fastapi.testclient import TestClient

    response = TestClient(app).post("/api/v1/notifications/", json={"notification_type": "RISK", "title": "x", "message": "y"}, follow_redirects=False)

    assert response.status_code == 401
    db = SessionLocal()
    try:
        count = db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.entity_type == "HTTP"))
        assert count == 1
    finally:
        db.close()
