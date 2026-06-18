from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.identity import User
from app.database.models.trading import Strategy
from app.domain.models.backtest_models import (
    PositionSizingCalculator,
    SlippageCalculator,
    SlippageConfig,
)
from app.services.backtest_service import BacktestService


def test_backtest_run_lifecycle():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        user = User(username="backtester", email="backtest@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
        strategy = Strategy(name="TestStrategy", code="TEST_STRATEGY", version="1.0", strategy_type="trend_following", status="ACTIVE")
        db.add_all([user, strategy])
        db.flush()

        service = BacktestService(db)
        run = service.create_run(
            user_id=user.id,
            strategy_id=strategy.id,
            name="Test Run",
            start_date=None,
            end_date=None,
            initial_capital=10000.0,
        )

        assert run.status == "PENDING"
        assert run.progress == 0.0
        assert run.initial_capital == 10000.0

        run.status = "RUNNING"
        run.progress = 50.0
        service.update_run_status(run.id, "RUNNING", 50.0)

        updated_run = service.get_run(run.id)
        assert updated_run.status == "RUNNING"
        assert updated_run.progress == 50.0
    finally:
        db.close()


def test_position_sizing_calculator():
    calc = PositionSizingCalculator(method="FIXED", value=0.1)
    assert calc.calculate_quantity(10000, 100) == 0.1

    calc = PositionSizingCalculator(method="PERCENTAGE", value=2.0)
    assert calc.calculate_quantity(10000, 100) == 2.0

    calc = PositionSizingCalculator(method="RISK_BASED", value=1.0)
    assert calc.calculate_quantity(10000, 100, stop_loss=95) == 20.0


def test_slippage_calculator():
    config = SlippageConfig(model="FIXED", max_slippage_pct=0.001)
    calc = SlippageCalculator(config)
    assert calc.calculate(100, 1000, 1000) == 0.1


def test_backtest_config_creation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        strategy = Strategy(name="ConfigTest", code="CONFIG_TEST", version="1.0", strategy_type="trend_following", status="ACTIVE")
        db.add(strategy)
        db.flush()

        service = BacktestService(db)
        config = service.create_config(
            strategy_id=strategy.id,
            name="Test Config",
            position_sizing_method="FIXED",
            position_size_value=0.1,
            max_positions=5,
            slippage_model={"model": "FIXED", "max_slippage_pct": 0.001},
            commission_model={"model": "FLAT", "taker_fee": 0.001},
        )

        assert config.name == "Test Config"
        assert config.position_sizing_method == "FIXED"
        assert config.position_size_value == 0.1
    finally:
        db.close()
