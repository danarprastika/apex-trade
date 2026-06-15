from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.domain.events.trading import OrderCreated, SignalGenerated
from app.domain.value_objects.trading import Confidence, Money, OrderSide, Price, Quantity, RiskScore


class RiskValidator(ABC):
    @abstractmethod
    def validate(self, risk_score: RiskScore, requested_position_size: float | None = None) -> tuple[bool, str]:
        """Validate if action is allowed based on risk profile."""
        pass


class DefaultRiskValidator(RiskValidator):
    def __init__(self, max_risk_per_trade: float = 2.0, max_daily_loss: float = 5.0, max_open_positions: int = 10):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_open_positions = max_open_positions

    def validate(self, risk_score: RiskScore, requested_position_size: float | None = None) -> tuple[bool, str]:
        max_score = 100.0 - (self.max_risk_per_trade * 10)
        if risk_score.value > max_score:
            return False, f"Risk score {risk_score.value} exceeds threshold"
        if requested_position_size and requested_position_size > 0:
            # Additional position size validation
            pass
        return True, "Risk validation passed"


class SignalProcessor:
    def calculate_position_size(
        self,
        confidence: Confidence,
        portfolio_value: Money,
        price: Price,
    ) -> Quantity:
        """Calculate position size based on confidence and portfolio value."""
        base_allocation = portfolio_value.amount * Decimal("0.02")  # 2% base
        confidence_multiplier = Decimal(str(confidence.value / 100))
        position_value = base_allocation * confidence_multiplier
        return Quantity(position_value / price.value)

    def calculate_risk_score(self, signal: SignalGenerated, market_volatility: float) -> RiskScore:
        """Calculate risk score for a signal."""
        # Simplified risk calculation - would be more complex in production
        signal_risk = 100.0 - signal.confidence
        volatility_risk = market_volatility * 50
        return RiskScore(min(100.0, signal_risk + volatility_risk))


class PositionCalculator:
    @staticmethod
    def calculate_pnl(
        entry_price: Price,
        exit_price: Price,
        quantity: Quantity,
        side: OrderSide,
    ) -> Money:
        """Calculate profit/loss for a closed position."""
        multiplier = Decimal("1") if side == OrderSide.buy else Decimal("-1")
        difference = exit_price.value - entry_price.value
        return Money(difference * quantity.value * multiplier)