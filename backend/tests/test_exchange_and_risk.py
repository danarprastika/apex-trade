from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.models.identity import User
from app.database.models.portfolio import Portfolio
from app.database.models.risk import RiskProfile
from app.services.exchange_service import ExchangeService


def test_exchange_service_sync_account_stores_real_balance_snapshot():
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
            api_key_encrypted="encrypted-key",
            api_secret_encrypted="encrypted-secret",
            is_testnet=True,
            status="ACTIVE",
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        class FakeBalanceClient:
            def load_markets(self):
                return None

            def fetch_balance(self):
                return {"total": {"USDT": "100.0"}, "free": {"USDT": "80.0"}, "used": {"USDT": "20.0"}}

            def fetch_positions(self):
                return [{"symbol": "BTCUSDT", "side": "LONG", "contracts": "1", "entryPrice": "50000", "markPrice": "51000", "unrealizedPnl": "1000", "leverage": "5"}]

        service = ExchangeService(db)
        service._build_client = lambda exchange, account: FakeBalanceClient()

        result = service.sync_account(account.id, user.id)

        assert result["status"] == "synced"
        assert result["balances"]["currencies"][0]["currency"] == "USDT"
        assert result["positions"][0]["symbol"] == "BTCUSDT"
        db.refresh(account)
        assert account.sync_status == "SYNCED"
        assert account.balance_snapshot["currencies"][0]["total"] == "100.0"
    finally:
        db.close()


def test_risk_service_veto_high_score_and_notional():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        user = User(username="riskuser", email="risk@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        db.add(user)
        db.flush()
        profile = RiskProfile(user_id=user.id, max_risk_per_trade=2.0, max_daily_loss=3.0, max_drawdown=10.0, max_open_positions=1)
        portfolio = Portfolio(user_id=user.id, total_value=1000, cash_balance=1000, risk_score=0)
        db.add_all([profile, portfolio])
        db.commit()

        from app.services.risk_service import RiskService

        high_risk = RiskService(db).evaluate(user.id, risk_score=90, requested_position_size=500)
        notional_risk = RiskService(db).evaluate(user.id, risk_score=1, requested_position_size=500)

        assert high_risk.allowed is False
        assert "risk score exceeds max_risk_per_trade" in high_risk.veto_reasons
        assert "risk score exceeds hard ceiling 85" in high_risk.veto_reasons
        assert notional_risk.allowed is False
        assert "requested notional exceeds max_risk_per_trade percentage of portfolio" in notional_risk.veto_reasons
    finally:
        db.close()
