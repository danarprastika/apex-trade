from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.models.identity import User
from app.database.models.trading import Order
from app.services.trading_safety.post_trade_validator import PostTradeValidator


def test_post_trade_validator_approves_valid():
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
        db.flush()

        order = Order(
            exchange_account_id=account.id,
            order_type="MARKET",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            status="FILLED",
            filled_quantity=1.0,
        )
        db.add(order)
        db.commit()

        validator = PostTradeValidator(db)

        class MockAdapter:
            def fetch_order(self, order_id: str, context: Any) -> Any:
                class MockOrder:
                    status = "filled"
                    average_fill_price = 50000.0
                    fee = 5.0
                    filled_quantity = 1.0
                return MockOrder()

        class MockContext:
            user_id: str = user.id
            exchange_id: str = exchange.id

        decision = validator.validate(order.id, MockAdapter(), MockContext())
        assert decision.approved is True
    finally:
        db.close()


def test_post_trade_validator_rejects_price_deviation():
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
        db.flush()

        order = Order(
            exchange_account_id=account.id,
            order_type="LIMIT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            status="FILLED",
            filled_quantity=1.0,
        )
        db.add(order)
        db.commit()

        validator = PostTradeValidator(db)

        class MockAdapter:
            def fetch_order(self, order_id: str, context: Any) -> Any:
                class MockOrder:
                    status = "filled"
                    average_fill_price = 52000.0
                    fee = 5.0
                    filled_quantity = 1.0
                return MockOrder()

        class MockContext:
            user_id: str = user.id
            exchange_id: str = exchange.id

        decision = validator.validate(order.id, MockAdapter(), MockContext())
        assert decision.approved is False
        assert any("Fill price deviation" in r for r in decision.reasons)
    finally:
        db.close()


def test_post_trade_validator_handles_missing_order():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    try:
        user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        db.add(user)
        db.flush()
        db.commit()

        validator = PostTradeValidator(db)

        class MockContext:
            user_id: str = user.id
            exchange_id: str = None

        decision = validator.validate("nonexistent-order-id", None, MockContext())
        assert decision.approved is False
        assert any("not found" in r for r in decision.reasons)
    finally:
        db.close()
