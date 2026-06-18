from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass
class Order:
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    filled_quantity: float = 0.0
    filled_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: Any = None
    slippage_cost: float = 0.0
    commission_cost: float = 0.0
    order_id: str = ""

    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity

    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    def is_partially_filled(self) -> bool:
        return self.status == OrderStatus.PARTIALLY_FILLED


@dataclass
class FillResult:
    order_id: str
    filled_quantity: float
    fill_price: float
    slippage: float
    commission: float
    timestamp: Any


class OrderSimulator:
    def __init__(self, slippage_calculator: Any, commission_calculator: Any, partial_fill_support: bool = True):
        self.slippage_calculator = slippage_calculator
        self.commission_calculator = commission_calculator
        self.partial_fill_support = partial_fill_support
        self.order_book: dict[str, list[Order]] = {}
        self.fill_history: list[FillResult] = []

    def submit_order(self, order: Order, candle: Any, avg_volume: float = 0.0) -> FillResult:
        if order.order_type == OrderType.MARKET:
            return self._execute_market(order, candle, avg_volume)
        elif order.order_type == OrderType.LIMIT:
            return self._execute_limit(order, candle, avg_volume)
        elif order.order_type == OrderType.STOP:
            return self._execute_stop(order, candle, avg_volume)
        raise ValueError(f"Unsupported order type: {order.order_type}")

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.order_book:
            for orders in self.order_book.values():
                for o in orders:
                    if o.order_id == order_id:
                        o.status = OrderStatus.CANCELLED
                        return True
        return False

    def _execute_market(self, order: Order, candle: Any, avg_volume: float) -> FillResult:
        if candle is None:
            raise ValueError("Cannot execute MARKET order without candle data")

        candle_volume = float(candle.volume) if hasattr(candle, "volume") else 0.0
        candle_open = float(candle.open) if hasattr(candle, "open") else 0.0
        candle_close = float(candle.close) if hasattr(candle, "close") else candle_open
        candle_high = float(candle.high) if hasattr(candle, "high") else candle_open
        candle_low = float(candle.low) if hasattr(candle, "low") else candle_open

        if order.side == OrderSide.BUY:
            execution_price = candle_high + self.slippage_calculator.calculate(candle_high, candle_volume, avg_volume)
            execution_price = min(execution_price, candle_high)
        else:
            execution_price = candle_low - self.slippage_calculator.calculate(candle_low, candle_volume, avg_volume)
            execution_price = max(execution_price, candle_low)

        slippage = abs(execution_price - candle_close)
        fill_qty = order.quantity

        commission = self.commission_calculator.calculate(fill_qty, execution_price, is_maker=False)

        order.filled_quantity = fill_qty
        order.filled_price = execution_price
        order.status = OrderStatus.FILLED
        order.slippage_cost = slippage * fill_qty
        order.commission_cost = commission

        fill = FillResult(
            order_id=order.order_id,
            filled_quantity=fill_qty,
            fill_price=execution_price,
            slippage=slippage,
            commission=commission,
            timestamp=candle.close_time if hasattr(candle, "close_time") else None,
        )
        self.fill_history.append(fill)
        return fill

    def _execute_limit(self, order: Order, candle: Any, avg_volume: float) -> FillResult:
        if candle is None:
            raise ValueError("Cannot execute LIMIT order without candle data")

        candle_close = float(candle.close) if hasattr(candle, "close") else 0.0
        candle_high = float(candle.high) if hasattr(candle, "high") else candle_close
        candle_low = float(candle.low) if hasattr(candle, "low") else candle_close
        candle_volume = float(candle.volume) if hasattr(candle, "volume") else 0.0

        target_price = order.price
        if target_price is None:
            raise ValueError("LIMIT order requires a price")

        filled = False
        if order.side == OrderSide.BUY and candle_low <= target_price:
            execution_price = target_price
            filled = True
        elif order.side == OrderSide.SELL and candle_high >= target_price:
            execution_price = target_price
            filled = True
        else:
            order.status = OrderStatus.PENDING
            return FillResult(
                order_id=order.order_id,
                filled_quantity=0.0,
                fill_price=target_price,
                slippage=0.0,
                commission=0.0,
                timestamp=candle.close_time if hasattr(candle, "close_time") else None,
            )

        slippage = self.slippage_calculator.calculate(execution_price, candle_volume, avg_volume) if filled else 0.0
        fill_qty = order.quantity
        commission = self.commission_calculator.calculate(fill_qty, execution_price, is_maker=True) if filled else 0.0

        order.filled_quantity = fill_qty
        order.filled_price = execution_price
        order.status = OrderStatus.FILLED if filled else OrderStatus.PENDING
        order.slippage_cost = slippage * fill_qty if filled else 0.0
        order.commission_cost = commission if filled else 0.0

        fill = FillResult(
            order_id=order.order_id,
            filled_quantity=fill_qty if filled else 0.0,
            fill_price=execution_price,
            slippage=slippage,
            commission=commission,
            timestamp=candle.close_time if hasattr(candle, "close_time") else None,
        )
        self.fill_history.append(fill)
        return fill

    def _execute_stop(self, order: Order, candle: Any, avg_volume: float) -> FillResult:
        if candle is None:
            raise ValueError("Cannot execute STOP order without candle data")

        candle_close = float(candle.close) if hasattr(candle, "close") else 0.0
        candle_high = float(candle.high) if hasattr(candle, "high") else candle_close
        candle_low = float(candle.low) if hasattr(candle, "low") else candle_close
        candle_volume = float(candle.volume) if hasattr(candle, "volume") else 0.0
        stop_price = order.stop_price

        if stop_price is None:
            raise ValueError("STOP order requires a stop_price")

        triggered = False
        if order.side == OrderSide.BUY and candle_high >= stop_price:
            triggered = True
        elif order.side == OrderSide.SELL and candle_low <= stop_price:
            triggered = True

        if not triggered:
            order.status = OrderStatus.PENDING
            return FillResult(
                order_id=order.order_id,
                filled_quantity=0.0,
                fill_price=stop_price,
                slippage=0.0,
                commission=0.0,
                timestamp=candle.close_time if hasattr(candle, "close_time") else None,
            )

        execution_price = stop_price
        slippage = self.slippage_calculator.calculate(stop_price, candle_volume, avg_volume)
        fill_qty = order.quantity
        commission = self.commission_calculator.calculate(fill_qty, execution_price, is_maker=False)

        order.filled_quantity = fill_qty
        order.filled_price = execution_price
        order.status = OrderStatus.FILLED
        order.slippage_cost = slippage * fill_qty
        order.commission_cost = commission

        fill = FillResult(
            order_id=order.order_id,
            filled_quantity=fill_qty,
            fill_price=execution_price,
            slippage=slippage,
            commission=commission,
            timestamp=candle.close_time if hasattr(candle, "close_time") else None,
        )
        self.fill_history.append(fill)
        return fill

    def get_order_book_snapshot(self, symbol: str) -> list[Order]:
        return self.order_book.get(symbol, [])
