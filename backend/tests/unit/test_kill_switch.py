from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.exchange import Exchange
from app.database.models.identity import User
from app.database.models.trading_safety import KillSwitchState
from app.domain.safety.value_objects import KillSwitchScope
from app.services.trading_safety.kill_switch_service import KillSwitchService


def test_kill_switch_service_global_enabled():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="admin", email="admin@example.com", password_hash="hash", role="SUPER_ADMIN", status="ACTIVE")
        db.add(user)
        db.commit()

        service = KillSwitchService(db)
        assert service.is_global_kill_enabled() is False

        from app.database.models.trading_safety import KillSwitchState
        state = KillSwitchState(scope=KillSwitchScope.GLOBAL.value, enabled=True, reason="test")
        db.add(state)
        db.commit()

        assert service.is_global_kill_enabled() is True
    finally:
        db.close()


def test_kill_switch_service_user_enabled():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        db.add(user)
        db.commit()

        service = KillSwitchService(db)
        assert service.is_user_kill_enabled(user.id) is False

        state = KillSwitchState(scope=KillSwitchScope.USER.value, scope_id=user.id, enabled=True, reason="test")
        db.add(state)
        db.commit()

        assert service.is_user_kill_enabled(user.id) is True
    finally:
        db.close()


def test_kill_switch_service_check_all():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        exchange = Exchange(name="Binance", exchange_type="binance", status="ACTIVE")
        db.add_all([user, exchange])
        db.commit()

        service = KillSwitchService(db)
        blocked, reasons = service.check_all(user.id, exchange.id, None)
        assert blocked is False
        assert reasons == []


        state = KillSwitchState(scope=KillSwitchScope.GLOBAL.value, enabled=True, reason="emergency")
        db.add(state)
        db.commit()

        blocked, reasons = service.check_all(user.id, exchange.id, None)
        assert blocked is True
        assert "GLOBAL" in reasons
    finally:
        db.close()


def test_kill_switch_service_authorization():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        wrong_role_user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        db.add(wrong_role_user)
        db.commit()

        service = KillSwitchService(db)
        with pytest.raises(Exception):
            service.trigger_kill(
                scope=KillSwitchScope.GLOBAL,
                scope_id=None,
                triggered_by=wrong_role_user.id,
                actor_role=wrong_role_user.role,
                ip_address=None,
                reason="test",
                expires_at=None,
            )
    finally:
        db.close()


def test_kill_switch_service_user_can_trigger_own():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        trader = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        db.add(trader)
        db.commit()

        service = KillSwitchService(db)
        service.trigger_kill(
            scope=KillSwitchScope.USER,
            scope_id=trader.id,
            triggered_by=trader.id,
            actor_role=trader.role,
            ip_address=None,
            reason="self triggered",
            expires_at=None,
        )

        assert service.is_user_kill_enabled(trader.id) is True
    finally:
        db.close()
