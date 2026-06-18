from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.models.identity import User
from app.database.models.portfolio import Portfolio
from app.database.models.risk import RiskProfile
from app.domain.safety.value_objects import SafetyContext
from app.services.trading_safety.kill_switch_service import KillSwitchService
from app.services.trading_safety.pre_trade_validator import PreTradeValidator


def test_pre_trade_validator_approves_valid():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        exchange = Exchange(name="Binance", exchange_type="binance", status="ACTIVE")
        db.add_all([user, exchange])
        db.flush()

        account = ExchangeAccount(
            user_id=user.id,
            exchange_id=exchange.id,
            api_key_encrypted="enc_key",
            api_secret_encrypted="enc_secret",
            status="ACTIVE",
        )
        portfolio = Portfolio(user_id=user.id, total_value=10000, cash_balance=10000, risk_score=0)
        risk_profile = RiskProfile(
            user_id=user.id,
            max_risk_per_trade=5.0,
            max_daily_loss=50.0,
            max_drawdown=10.0,
            max_open_positions=10,
        )
        db.add_all([account, portfolio, risk_profile])
        db.commit()

        kill_service = KillSwitchService(db)
        validator = PreTradeValidator(db, kill_service)

        context = SafetyContext(
            user_id=user.id,
            exchange_account_id=account.id,
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            price=50000.0,
        )

        decision = validator.validate(context)
        assert decision.approved is True
    finally:
        db.close()


def test_pre_trade_validator_rejects_zero_quantity():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        exchange = Exchange(name="Binance", exchange_type="binance", status="ACTIVE")
        db.add_all([user, exchange])
        db.flush()

        account = ExchangeAccount(
            user_id=user.id,
            exchange_id=exchange.id,
            api_key_encrypted="enc_key",
            api_secret_encrypted="enc_secret",
            status="ACTIVE",
        )
        db.add(account)
        db.commit()

        kill_service = KillSwitchService(db)
        validator = PreTradeValidator(db, kill_service)

        context = SafetyContext(
            user_id=user.id,
            exchange_account_id=account.id,
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0,
            price=50000.0,
        )

        decision = validator.validate(context)
        assert decision.approved is False
        assert any("Quantity must be greater than zero" in r for r in decision.reasons)
    finally:
        db.close()


def test_pre_trade_validator_blocks_on_global_kill_switch():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        exchange = Exchange(name="Binance", exchange_type="binance", status="ACTIVE")
        db.add_all([user, exchange])
        db.flush()

        account = ExchangeAccount(
            user_id=user.id,
            exchange_id=exchange.id,
            api_key_encrypted="enc_key",
            api_secret_encrypted="enc_secret",
            status="ACTIVE",
        )
        db.add(account)
        db.commit()

        from app.database.models.trading_safety import KillSwitchState
        from app.domain.safety.value_objects import KillSwitchScope
        state = KillSwitchState(scope=KillSwitchScope.GLOBAL.value, enabled=True, reason="test")
        db.add(state)
        db.commit()

        kill_service = KillSwitchService(db)
        validator = PreTradeValidator(db, kill_service)

        context = SafetyContext(
            user_id=user.id,
            exchange_account_id=account.id,
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=1.0,
            price=50000.0,
        )

        decision = validator.validate(context)
        assert decision.approved is False
        assert any("Global kill switch" in r for r in decision.reasons)
    finally:
        db.close()
