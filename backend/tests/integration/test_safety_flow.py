from __future__ import annotations

from typing import Any

from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.models.identity import User
from app.database.models.portfolio import Portfolio
from app.database.models.risk import RiskProfile
from app.database.models.trading import Order
from app.database.models.trading_safety import KillSwitchState
from app.domain.safety.value_objects import KillSwitchScope, SafetyContext
from app.services.trading_safety import SafetyOrchestrator


def test_full_safety_flow_integration(integration_db_session):
    db = integration_db_session

    user = User(username="trader", email="trader@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    admin = User(username="admin", email="admin@example.com", password_hash="hash", role="ADMIN", status="ACTIVE")
    exchange = Exchange(name="Binance", exchange_type="binance", status="ACTIVE")
    db.add_all([user, admin, exchange])
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
    db.flush()
    db.commit()

    orchestrator = SafetyOrchestrator(db)
    context = SafetyContext(
        user_id=user.id,
        exchange_account_id=account.id,
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=1.0,
        price=50000.0,
    )

    decision = orchestrator.validate_pre_trade(context)
    assert decision.approved is True


def test_kill_switch_blocks_trading_integration(integration_db_session):
    db = integration_db_session

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

    kill_state = KillSwitchState(scope=KillSwitchScope.GLOBAL.value, enabled=True, reason="Emergency stop")
    db.add(kill_state)
    db.commit()

    orchestrator = SafetyOrchestrator(db)

    blocked, reasons = orchestrator.kill_switch.check_all(user.id, exchange.id, None)
    assert blocked is True
    assert "GLOBAL" in reasons


def test_post_trade_validation_integration(integration_db_session):
    db = integration_db_session

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
    db.flush()
    db.commit()

    orchestrator = SafetyOrchestrator(db)

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

    decision = orchestrator.validate_post_trade(order.id, MockAdapter(), MockContext())
    assert decision.approved is False


def test_health_check_aggregation(integration_db_session):
    db = integration_db_session

    orchestrator = SafetyOrchestrator(db)

    health = orchestrator.get_health_status()
    assert "status" in health
    assert "components" in health
    assert "kill_switch" in health["components"]
    assert "reconciliation" in health["components"]
    assert "market_data_quality" in health["components"]
    assert "exposure_monitor" in health["components"]
