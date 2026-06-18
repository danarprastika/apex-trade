from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.trading import Strategy, StrategyParameter
from app.database.repositories.trading_repository import StrategyRepository
from app.domain.strategies.types import PluginHealthStatus, PluginLifecycleState, SignalType
from app.domain.strategies.versioning import SemanticVersion
from app.services.plugin_registry import PluginRegistry
from app.services.strategy_config_manager import StrategyConfigManager
from app.services.strategy_engine import StrategyEngine
from plugins.arbitrage.plugin import ArbitragePlugin
from plugins.custom.sandbox import CustomSandboxPlugin
from plugins.scalping.plugin import ScalpingPlugin


def test_arbitrage_plugin_detects_fee_aware_opportunity() -> None:
    plugin = ArbitragePlugin()
    plugin.initialize({"min_profit_pct": 0.0005, "max_slippage_pct": 0.0001, "min_spread_pct": 0.0005})

    result = plugin.analyze(
        {
            "quotes": [
                {"exchange": "binance", "bid": 99.9, "ask": 100.0, "maker_fee": 0.0005, "taker_fee": 0.001},
                {"exchange": "bybit", "bid": 101.0, "ask": 101.1, "maker_fee": 0.0004, "taker_fee": 0.0008},
            ]
        }
    )

    assert result is not None
    assert result.signal_type == SignalType.BUY
    assert result.metadata["buy_exchange"] == "binance"
    assert result.metadata["sell_exchange"] == "bybit"
    assert result.metadata["net_profit_pct"] > 0


def test_arbitrage_plugin_rejects_opportunity_after_fees() -> None:
    plugin = ArbitragePlugin()
    plugin.initialize({"min_profit_pct": 0.001})

    result = plugin.analyze(
        {
            "quotes": [
                {"exchange": "binance", "bid": 99.9, "ask": 100.0, "maker_fee": 0.001, "taker_fee": 0.001},
                {"exchange": "bybit", "bid": 100.25, "ask": 100.35, "maker_fee": 0.001, "taker_fee": 0.001},
            ]
        }
    )

    assert result is None


def test_custom_sandbox_executes_safe_strategy() -> None:
    plugin = CustomSandboxPlugin(code="safe")
    plugin.initialize(
        {
            "custom_code": "def apex_strategy(market_data):\n    return {'signal_type': 'BUY', 'confidence': 70, 'entry_price': market_data['close'], 'reason': 'safe'}\n",
            "max_execution_ms": 100,
        }
    )

    result = plugin.analyze({"close": 123.45})

    assert result is not None
    assert result.signal_type == SignalType.BUY
    assert result.entry_price == 123.45


def test_custom_sandbox_rejects_unsafe_code() -> None:
    plugin = CustomSandboxPlugin(code="unsafe")

    validation = plugin.validate_config({"custom_code": "import os\n\ndef apex_strategy(market_data):\n    return None\n"})

    assert validation.valid is False
    assert any("import os" in error for error in validation.errors)

    validation = plugin.validate_config({"custom_code": "def apex_strategy(market_data):\n    return eval('1+1')\n"})
    assert validation.valid is False
    assert any("eval" in error for error in validation.errors)


def test_strategy_engine_records_plugin_health() -> None:
    registry = PluginRegistry()
    plugin = ScalpingPlugin()
    registry.register(plugin)
    registry.activate("scalping")
    engine = StrategyEngine(registry)

    candles = [{"close": 100 - i, "high": 101, "low": 99, "volume": 1000} for i in range(20)]
    engine.analyze_symbol("BTCUSDT", "1m", {"candles": candles, "orderbook": {"bid": 80.0, "ask": 80.05}})

    health = registry.get_health("scalping")
    assert health is not None
    assert health.lifecycle_state == PluginLifecycleState.activated
    assert health.health_status == PluginHealthStatus.healthy
    assert health.executions >= 1


def test_strategy_config_manager_persists_schema_and_parameters() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        strategy = Strategy(
            name="Scalping",
            code="scalping",
            version="1.0.0",
            strategy_type="scalping",
            status="ACTIVE",
        )
        db.add(strategy)
        db.flush()

        manager = StrategyConfigManager(StrategyRepository(db), PluginRegistry())
        schema = manager.get_parameters_schema("scalping")
        saved_schema = manager.get_saved_parameter_schema("scalping")
        manager.update_parameters(
            "scalping",
            {
                "spread_threshold": 0.001,
                "rsi_period": 9,
                "rsi_extreme": 25,
                "profit_target": 0.005,
            },
        )
        parameters = db.query(StrategyParameter).filter_by(strategy_id=strategy.id).all()

        assert saved_schema == schema
        assert {parameter.parameter_name for parameter in parameters} == {
            "spread_threshold",
            "rsi_period",
            "rsi_extreme",
            "profit_target",
        }
    finally:
        db.close()


def test_semantic_version_migration_blocks_major_without_approval() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        manager = StrategyConfigManager(StrategyRepository(db), PluginRegistry())
        params = {
            "spread_threshold": 0.001,
            "rsi_period": 9,
            "rsi_extreme": 25,
            "profit_target": 0.005,
        }

        try:
            manager.migrate_parameters("scalping", "1.0.0", "2.0.0", params)
        except ValueError as exc:
            assert "Major strategy version migration" in str(exc)
        else:
            raise AssertionError("Major migration was not blocked")

        migrated = manager.migrate_parameters(
            "scalping",
            "1.0.0",
            "2.0.0",
            params,
            allow_major_migration=True,
            migration_rules={"max_position_time": 120},
        )
        assert migrated["max_position_time"] == 120
    finally:
        db.close()


def test_semantic_version_parse_and_compare() -> None:
    assert str(SemanticVersion.parse("1.2.3")) == "1.2.3"
    assert SemanticVersion.parse("1.2.3").is_compatible_with(SemanticVersion.parse("1.9.0"))
    assert not SemanticVersion.parse("1.2.3").is_compatible_with(SemanticVersion.parse("2.0.0"))
    assert SemanticVersion.parse("1.2.3") < SemanticVersion.parse("1.2.4")
