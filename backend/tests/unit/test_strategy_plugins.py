from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import ValidationError
from app.database.base import Base
from app.domain.entities.strategy import StrategyType
from app.domain.strategies.types import SignalType
from app.schemas.trading import StrategyCreate
from app.services.plugin_registry import PluginRegistry
from app.services.trading_service import StrategyService
from plugins.breakout.plugin import BreakoutPlugin
from plugins.mean_reversion.plugin import MeanReversionPlugin
from plugins.scalping.plugin import ScalpingPlugin
from plugins.trend_following.plugin import TrendFollowingPlugin


def test_scalping_is_supported_strategy_type() -> None:
    assert StrategyType.scalping.value == "scalping"
    assert StrategyType.scalping in StrategyType


def test_scalping_plugin_metadata_uses_strategy_type_enum() -> None:
    plugin = ScalpingPlugin()

    assert plugin.metadata.strategy_type == StrategyType.scalping
    assert plugin.metadata.strategy_type.value == "scalping"


def test_plugin_registry_groups_scalping_by_type() -> None:
    registry = PluginRegistry()

    registry.register(ScalpingPlugin())

    assert registry.get_plugin_codes() == ["scalping"]
    assert [plugin.metadata.strategy_type.value for plugin in registry.get_plugins_by_type("scalping")] == ["scalping"]


def test_strategy_schema_accepts_scalping_type() -> None:
    payload = StrategyCreate(
        name="Scalping",
        code="scalping",
        version="1.0.0",
        strategy_type="scalping",
        description="Scalping strategy",
    )

    assert payload.strategy_type == StrategyType.scalping


def test_strategy_service_creates_scalping_strategy() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        service = StrategyService(db)
        strategy = service.create(
            name="Scalping",
            code="scalping",
            version="1.0.0",
            strategy_type="scalping",
            description="Scalping strategy",
        )

        assert strategy.strategy_type == StrategyType.scalping.value
        assert service.list_by_type("scalping") == [strategy]
    finally:
        db.close()


def test_strategy_service_rejects_unknown_strategy_type() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        service = StrategyService(db)

        try:
            service.create(
                name="Invalid Strategy",
                code="invalid_strategy",
                version="1.0.0",
                strategy_type="unknown",
                description="Invalid strategy type",
            )
        except ValidationError as exc:
            assert "Invalid strategy_type" in str(exc)
        else:
            raise AssertionError("StrategyService accepted an unknown strategy type")
    finally:
        db.close()


class TestTrendFollowingPlugin:
    @pytest.fixture
    def plugin(self) -> TrendFollowingPlugin:
        return TrendFollowingPlugin()

    def test_metadata(self, plugin: TrendFollowingPlugin) -> None:
        metadata = plugin.metadata
        assert metadata.name == "Trend Following"
        assert metadata.strategy_type == "trend_following"
        assert metadata.version == "1.0.0"
        assert metadata.min_lookback_periods == 50

    def test_validate_config_valid(self, plugin: TrendFollowingPlugin) -> None:
        result = plugin.validate_config({"fast_ma_period": 9, "slow_ma_period": 21})
        assert result.valid is True
        assert result.errors == []

    def test_validate_config_invalid_fast_slow(self, plugin: TrendFollowingPlugin) -> None:
        result = plugin.validate_config({"fast_ma_period": 21, "slow_ma_period": 9})
        assert result.valid is False
        assert "fast_ma_period must be less than slow_ma_period" in result.errors

    def test_analyze_no_signal_insufficient_data(self, plugin: TrendFollowingPlugin) -> None:
        candles = [{"close": 100.0 + i, "high": 101.0 + i, "low": 99.0 + i, "volume": 1000} for i in range(10)]
        result = plugin.analyze({"candles": candles})
        assert result is None

    def test_analyze_bullish_signal(self, plugin: TrendFollowingPlugin) -> None:
        plugin.initialize({"fast_ma_period": 5, "slow_ma_period": 10})
        candles = []
        for _ in range(10):
            candles.append({"close": 100.0, "high": 101, "low": 99, "volume": 1000})
        for _ in range(10):
            candles.append({"close": 102.0, "high": 103, "low": 101, "volume": 1000})
        candles.append({"close": 120.0, "high": 121, "low": 119, "volume": 1000})
        result = plugin.analyze({"candles": candles})
        assert result is not None
        assert result.signal_type == SignalType.BUY


class TestMeanReversionPlugin:
    @pytest.fixture
    def plugin(self) -> MeanReversionPlugin:
        return MeanReversionPlugin()

    def test_metadata(self, plugin: MeanReversionPlugin) -> None:
        assert plugin.metadata.strategy_type == "mean_reversion"

    def test_validate_config_valid(self, plugin: MeanReversionPlugin) -> None:
        result = plugin.validate_config({
            "bb_period": 20,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
        })
        assert result.valid is True

    def test_analyze_no_signal_normal_rsi(self, plugin: MeanReversionPlugin) -> None:
        plugin.initialize({"bb_period": 20, "rsi_period": 14, "rsi_overbought": 70, "rsi_oversold": 30})
        candles = [{"close": 100.0 + (i % 5), "high": 101, "low": 99, "volume": 1000} for i in range(100)]
        result = plugin.analyze({"candles": candles})
        assert result is None


class TestBreakoutPlugin:
    @pytest.fixture
    def plugin(self) -> BreakoutPlugin:
        return BreakoutPlugin()

    def test_metadata(self, plugin: BreakoutPlugin) -> None:
        assert plugin.metadata.strategy_type == "breakout"

    def test_analyze_breakout(self, plugin: BreakoutPlugin) -> None:
        plugin.initialize({"lookback_periods": 20, "breakout_threshold": 0.02, "volume_multiplier": 1.5})
        base_price = 100.0
        candles = []
        for _ in range(20):
            candles.append({"close": base_price, "high": base_price + 0.5, "low": base_price - 0.5, "volume": 1000})
        candles.append({"close": 100.0, "high": 100.5, "low": 99.5, "volume": 1000})
        candles.append({"close": 103.0, "high": 103.5, "low": 102.5, "volume": 3000})
        result = plugin.analyze({"candles": candles})
        assert result is not None
        assert result.signal_type == SignalType.BUY


class TestScalpingPlugin:
    @pytest.fixture
    def plugin(self) -> ScalpingPlugin:
        return ScalpingPlugin()

    def test_metadata(self, plugin: ScalpingPlugin) -> None:
        assert plugin.metadata.strategy_type == "scalping"

    def test_validate_config(self, plugin: ScalpingPlugin) -> None:
        result = plugin.validate_config({
            "spread_threshold": 0.001,
            "rsi_period": 9,
            "rsi_extreme": 25,
            "profit_target": 0.005,
        })
        assert result.valid is True

    def test_analyze_scalping_buy(self, plugin: ScalpingPlugin) -> None:
        plugin.initialize({"spread_threshold": 0.002, "rsi_period": 9, "rsi_extreme": 25, "profit_target": 0.005})
        falling_prices = [100 - i for i in range(10, 0, -1)]
        candles = [{"close": p, "high": p + 1, "low": p - 1, "volume": 1000} for p in falling_prices]
        for _ in range(10):
            candles.append({"close": candles[-1]["close"] - 0.5, "high": 100, "low": 90, "volume": 1000})
        orderbook = {"bid": 90.0, "ask": 90.1}
        result = plugin.analyze({"candles": candles, "orderbook": orderbook})
        assert result is not None
        assert result.signal_type == SignalType.BUY
