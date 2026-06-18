from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import FeatureDisabledError
from app.database.base import Base
from app.database.models.audit import AuditLog
from app.services.paper_trading_service import PaperTradingService
from app.services.trading_service import ExecutionService


class DisabledFeatureFlagService:
    def require_enabled(self, key, user=None, environment=None):
        raise FeatureDisabledError(f"Feature '{key}' is disabled: globally_disabled")


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()


def test_paper_trading_blocked_when_feature_flag_disabled_and_audited():
    db = _session()
    try:
        service = PaperTradingService(db, feature_flag_service=DisabledFeatureFlagService())

        try:
            service.execute_order(
                user_id="user-1",
                market_pair_id="market-1",
                strategy_id="strategy-1",
                side="BUY",
                quantity=1,
                price=100,
            )
        except FeatureDisabledError as exc:
            assert "paper_trading.enabled" in str(exc.detail)
        else:
            raise AssertionError("paper order should be blocked")

        audit = db.query(AuditLog).filter(AuditLog.action == "PAPER_TRADING_BLOCKED").one()
        assert audit.user_id == "user-1"
        assert audit.new_value["flag_key"] == "paper_trading.enabled"
    finally:
        db.close()


def test_live_trading_blocked_when_feature_flag_disabled_and_audited():
    db = _session()
    try:
        service = ExecutionService(db, feature_flag_service=DisabledFeatureFlagService())

        try:
            service.create_order(
                exchange_account_id="account-1",
                order_type="MARKET",
                side="BUY",
                quantity=1,
                price=100,
                user_id="user-1",
            )
        except FeatureDisabledError as exc:
            assert "live_trading.enabled" in str(exc.detail)
        else:
            raise AssertionError("live order should be blocked")

        audit = db.query(AuditLog).filter(AuditLog.action == "LIVE_TRADING_BLOCKED").one()
        assert audit.user_id == "user-1"
        assert audit.new_value["flag_key"] == "live_trading.enabled"
    finally:
        db.close()
