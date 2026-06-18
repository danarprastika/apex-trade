from __future__ import annotations

from app.domain.strategies.base import StrategyPlugin
from plugins.arbitrage.plugin import ArbitragePlugin
from plugins.breakout.plugin import BreakoutPlugin
from plugins.custom.sandbox import CustomSandboxPlugin
from plugins.mean_reversion.plugin import MeanReversionPlugin
from plugins.scalping.plugin import ScalpingPlugin
from plugins.trend_following.plugin import TrendFollowingPlugin

__all__ = [
    "StrategyPlugin",
    "get_builtin_plugins",
    "ARBITRAGE_CODE",
    "TREND_FOLLOWING_CODE",
    "MEAN_REVERSION_CODE",
    "BREAKOUT_CODE",
    "SCALPING_CODE",
    "CUSTOM_CODE",
]

ARBITRAGE_CODE = "arbitrage"
TREND_FOLLOWING_CODE = "trend_following"
MEAN_REVERSION_CODE = "mean_reversion"
BREAKOUT_CODE = "breakout"
SCALPING_CODE = "scalping"
CUSTOM_CODE = "custom"


def get_builtin_plugins() -> dict[str, type[StrategyPlugin]]:
    """Return mapping of strategy codes to plugin classes."""
    return {
        ARBITRAGE_CODE: ArbitragePlugin,
        TREND_FOLLOWING_CODE: TrendFollowingPlugin,
        MEAN_REVERSION_CODE: MeanReversionPlugin,
        BREAKOUT_CODE: BreakoutPlugin,
        SCALPING_CODE: ScalpingPlugin,
        CUSTOM_CODE: CustomSandboxPlugin,
    }