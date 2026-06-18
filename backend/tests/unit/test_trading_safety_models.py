
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.exchange import Exchange
from app.database.models.identity import User
from app.database.models.trading_safety import KillSwitchState, OrderReconciliationLog


def test_trading_safety_safety_context_creation():
    from app.domain.safety.value_objects import SafetyContext

    context = SafetyContext(
        user_id="user-123",
        exchange_account_id="account-456",
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1.0,
        price=50000.0,
    )
    assert context.user_id == "user-123"
    assert context.quantity == 1.0


def test_trading_safety_safety_decision_rejection():
    from app.domain.safety.value_objects import SafetyDecision, ValidationLayer

    decision = SafetyDecision()
    decision.add_rejection(ValidationLayer.KILL_SWITCH, "Test rejection")
    assert decision.approved is False
    assert "Test rejection" in decision.reasons


def test_trading_safety_kill_switch_models():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        db.add(user)
        db.commit()

        state = KillSwitchState(scope="GLOBAL", enabled=True, reason="test", triggered_by=user.id)
        db.add(state)
        db.commit()

        assert state.enabled is True
        assert state.scope == "GLOBAL"
    finally:
        db.close()


def test_trading_safety_reconciliation_models():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        exchange = Exchange(name="Binance", exchange_type="binance", status="ACTIVE")
        db.add_all([user, exchange])
        db.flush()

        log = OrderReconciliationLog(
            order_id="order-123",
            exchange_id=exchange.id,
            user_id=user.id,
            expected_status="FILLED",
            actual_status="NEW",
            discrepancy_detected=True,
        )
        db.add(log)
        db.commit()

        assert log.discrepancy_detected is True
    finally:
        db.close()
