from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ExchangeCapability:
    exchange_id: str
    exchange_name: str
    asset_classes: tuple[str, ...] = ("CRYPTO",)
    spot: bool = True
    margin: bool = False
    futures: bool = False
    stocks: bool = False
    forex: bool = False
    order_book: bool = True
    funding_rate: bool = False
    open_interest: bool = False
    submit_order: bool = False
    cancel_order: bool = False
    modify_order: bool = False
    fetch_order: bool = False
    fetch_positions: bool = False
    fetch_balances: bool = True
    supported_order_types: tuple[str, ...] = ("MARKET", "LIMIT")
    supported_time_in_force: tuple[str, ...] = ("GTC",)
    supported_timeframes: tuple[str, ...] = ("1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w", "1M")


@dataclass(frozen=True)
class ExchangeOperationContext:
    exchange_id: str
    exchange_name: str
    operation: str
    user_id: str | None = None
    account_id: str | None = None
    symbol: str | None = None
    idempotency_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UnifiedCandle:
    exchange_id: str
    exchange_name: str
    source_symbol: str
    normalized_symbol: str
    base_asset: str
    quote_asset: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float | None = None
    trade_count: int | None = None
    source_timestamp: datetime | None = None
    received_at: datetime | None = None
    data_quality_score: float = 1.0


@dataclass(frozen=True)
class UnifiedTicker:
    exchange_id: str
    exchange_name: str
    source_symbol: str
    normalized_symbol: str
    last_price: float | None = None
    bid_price: float | None = None
    ask_price: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    volume_24h: float | None = None
    quote_volume_24h: float | None = None
    price_change_24h: float | None = None
    source_timestamp: datetime | None = None
    received_at: datetime | None = None


@dataclass(frozen=True)
class OrderBookLevel:
    price: float
    quantity: float


@dataclass(frozen=True)
class UnifiedOrderBook:
    exchange_id: str
    exchange_name: str
    source_symbol: str
    normalized_symbol: str
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    captured_at: datetime
    depth_level: int | None = None


@dataclass(frozen=True)
class UnifiedBalance:
    exchange_id: str
    exchange_name: str
    user_id: str
    account_id: str
    currency: str
    free: float
    used: float
    total: float
    available: float | None = None
    locked: float | None = None
    borrowed: float | None = None
    last_price: float | None = None
    valuation_currency: str | None = None
    estimated_value: float | None = None
    captured_at: datetime | None = None


@dataclass(frozen=True)
class UnifiedPosition:
    exchange_id: str
    exchange_name: str
    user_id: str
    account_id: str
    source_symbol: str
    normalized_symbol: str
    quantity: float
    entry_price: float | None = None
    current_price: float | None = None
    mark_price: float | None = None
    side: str | None = None
    leverage: float | None = None
    margin_used: float | None = None
    unrealized_pnl: float | None = None
    realized_pnl: float | None = None
    liquidation_price: float | None = None
    captured_at: datetime | None = None


@dataclass(frozen=True)
class UnifiedOrder:
    internal_order_id: str
    idempotency_key: str
    client_order_id: str | None
    exchange_order_id: str | None
    user_id: str | None
    exchange_account_id: str | None
    exchange_id: str
    exchange_name: str
    source: str = "signal"
    strategy_id: str | None = None
    signal_id: str | None = None
    execution_source: str | None = None
    routing_decision_id: str | None = None
    failover_attempt: int = 0
    primary_exchange_id: str | None = None
    fallback_exchange_id: str | None = None
    source_symbol: str | None = None
    normalized_symbol: str | None = None
    base_asset: str | None = None
    quote_asset: str | None = None
    asset_class: str | None = None
    side: str | None = None
    order_type: str | None = None
    time_in_force: str | None = None
    quantity: float | None = None
    quote_quantity: float | None = None
    price: float | None = None
    trigger_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    status: str = "NEW"
    raw_status: str | None = None
    filled_quantity: float = 0.0
    remaining_quantity: float | None = None
    average_price: float | None = None
    last_fill_price: float | None = None
    last_fill_time: datetime | None = None
    fee_currency: str | None = None
    fee_amount: float | None = None
    commission: float | None = None
    slippage: float | None = None
    notional_value: float | None = None
    created_at: datetime | None = None
    submitted_at: datetime | None = None
    accepted_at: datetime | None = None
    filled_at: datetime | None = None
    cancelled_at: datetime | None = None
    updated_at: datetime | None = None
    risk_decision_id: str | None = None
    pre_trade_check_id: str | None = None
    kill_switch_checked_at: datetime | None = None


@dataclass(frozen=True)
class ExchangeHealth:
    exchange_id: str
    exchange_name: str
    available: bool
    latency_ms: float | None = None
    success_rate: float | None = None
    error_rate: float | None = None
    rate_limit_remaining: float | None = None
    last_checked_at: datetime | None = None
    last_error: str | None = None
