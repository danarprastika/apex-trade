# Module Architecture

## 1. Trading Module

**Bounded Context**: Order execution and trade lifecycle management

```yaml
border: trading
responsibility: >
  Manage the complete lifecycle of orders from creation to execution.
  Handle trade recording, confirmation, and settlement.

aggregates:
  - OrderAggregate
    root: Order
    members:
      - OrderLine
      - Fee
      - ExecutionReport
    invariants:
      - Order.quantity > 0
      - Order.limit_price > 0 if type in [LIMIT, STOP_LIMIT]
      - Order.status transitions are valid
      - Sum of filled quantities <= order.quantity

entities:
  - Order
    fields:
      id: UUID [PK]
      symbol: Symbol
      side: OrderSide
      type: OrderType
      quantity: Quantity
      filled_quantity: Quantity
      limit_price: Price | None
      stop_price: Price | None
      time_in_force: TimeInForce
      status: OrderStatus
      exchange_order_id: str
      exchange: str
      created_at: UTCDateTime
      updated_at: UTCDateTime
      expires_at: UTCDateTime | None
    methods:
      - fill(quantity: Quantity, price: Price) -> ExecutionReport
      - cancel(reason: str) -> CancellationResult
      - is_active() -> bool
      - is_complete() -> bool

  - Trade
    fields:
      id: UUID [PK]
      order_id: UUID [FK]
      symbol: Symbol
      side: OrderSide
      quantity: Quantity
      price: Price
      fee: Price
      fee_currency: Currency
      exchange_trade_id: str
      executed_at: UTCDateTime
      created_at: UTCDateTime

  - ExecutionReport
    fields:
      order_id: UUID
      status: OrderStatus
      filled_quantity: Quantity
      average_price: Price
      timestamp: UTCDateTime

value_objects:
  - OrderSide: Literal[BUY, SELL]
  - OrderType: Literal[MARKET, LIMIT, STOP_LOSS, STOP_LIMIT, TAKE_PROFIT]
  - OrderStatus: Literal[PENDING, OPEN, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED, EXPIRED]
  - TimeInForce: Literal[GTC, IOC, FOK, DAY]
  - Quantity: Decimal (non-negative, constrained)
  - Price: Decimal (non-negative, constrained)

domain_services:
  - OrderValidationService
    + validate_order_constraints(order: Order) -> ValidationResult
    + check_balance_availability(order: Order, balance: Balance) -> bool
    + verify_risk_limits(order: Order, risk_context: RiskContext) -> RiskCheckResult

  - OrderMatchingService
    + match_order(order: Order, book: OrderBook) -> list[ExecutionReport]
    + calculate_execution(order: Order, ticker: MarketTicker) -> Price

repositories:
  - OrderRepository (interface)
    + save(order: Order) -> None
    + find_by_id(id: UUID) -> Order | None
    + find_by_portfolio(portfolio_id: UUID) -> list[Order]
    + find_pending_orders(symbol: Symbol) -> list[Order]
    + find_active_orders() -> list[Order]

  - TradeRepository (interface)
    + save(trade: Trade) -> None
    + find_by_order(order_id: UUID) -> list[Trade]
    + find_by_symbol(symbol: Symbol, start, end) -> list[Trade]

domain_events:
  - OrderCreated { order: Order }
  - OrderOpened { order: Order }
  - OrderPartiallyFilled { order: Order, execution: ExecutionReport }
  - OrderFilled { order: Order, executions: list[ExecutionReport] }
  - OrderCancelled { order: Order, reason: str }
  - OrderRejected { order: Order, reason: str }
  - TradeExecuted { trade: Trade }
```

## 2. Market Data Module

**Bounded Context**: Collecting, normalizing, and distributing market data

```yaml
border: market_data
responsibility: >
  Ingest market data from multiple sources, normalize to unified format,
  cache efficiently, and provide through pub/sub for real-time consumers.

aggregates:
  - PriceAggregate
    root: PriceTicker
    members:
      - PricePoint (bid, ask, last)
      - Volume24h
      - PriceChange

entities:
  - Candle
    fields:
      id: UUID [PK]
      symbol: Symbol
      timeframe: Timeframe
      open: Price
      high: Price
      low: Price
      close: Price
      volume: Quantity
      trades_count: int
      timestamp: UTCDateTime
      created_at: UTCDateTime
      source: str  # exchange identifier

  - OrderBook
    fields:
      symbol: Symbol
      exchange: str
      timestamp: UTCDateTime
      bids: list[PriceLevel]
      asks: list[PriceLevel]
      spread: Price
      spread_percent: Decimal

  - PriceLevel
    fields:
      price: Price
      quantity: Quantity

  - TradeTick
    fields:
      id: UUID [PK]
      symbol: Symbol
      exchange: str
      price: Price
      quantity: Quantity
      side: OrderSide
      timestamp: UTCDateTime

value_objects:
  - Timeframe: Literal[1m, 5m, 15m, 1h, 4h, 1d, 1w]
  - Price: Decimal (9 decimal places, precision 2 for display)
  - Volume: Decimal

domain_services:
  - CandleAggregationService
    + aggregate_trades_to_candle(trades: list[TradeTick], tf: Timeframe) -> Candle
    + resample_candles(candles: list[Candle], tf: Timeframe) -> list[Candle]

  - DataNormalizationService
    + normalize_ticker(raw: dict, exchange: str) -> PriceTicker
    + normalize_candle(raw: dict, exchange: str) -> Candle

  - BookSnapshotService
    + aggregate_orderbook_snapshots(snapshots: list[OrderBook]) -> OrderBook

repositories:
  - MarketDataRepository (interface)
    + save_candles(candles: list[Candle]) -> int  # returns count saved
    + get_candles(symbol: Symbol, timeframe: Timeframe, start, end) -> list[Candle]
    + get_latest_candle(symbol: Symbol, timeframe: Timeframe) -> Candle | None
    + save_trade_ticks(ticks: list[TradeTick]) -> int
    + get_recent_ticks(symbol: Symbol, limit) -> list[TradeTick]
    + save_orderbook_snapshot(book: OrderBook) -> None
    + get_latest_orderbook(symbol: Symbol) -> OrderBook | None

domain_events:
  - MarketTickReceived { tick: TradeTick }
  - CandleCompleted { candle: Candle }
  - OrderBookUpdated { book: OrderBook }
  - PriceAlertTriggered { symbol: Symbol, price: Price, condition: str }
```

## 3. Portfolio Module

**Bounded Context**: Portfolio valuation, asset tracking, and P&L calculation

```yaml
border: portfolio
responsibility: >
  Track user's portfolio value, asset allocation, and historical performance.
  Calculate P&L (realized and unrealized), risk metrics, and generate reports.

aggregates:
  - PortfolioAggregate
    root: Portfolio
    members:
      - Balance (per currency)
      - Position (per open trade)
      - AssetAllocation
      - PerformanceMetrics
    invariants:
      - Balance.available >= 0
      - Balance.locked >= 0
      - Balance.available + Balance.locked = Balance.total
      - Position.quantity > 0 for open positions

entities:
  - Portfolio
    fields:
      id: UUID [PK]
      name: str
      base_currency: Currency
      created_at: UTCDateTime
      updated_at: UTCDateTime

  - Position
    fields:
      id: UUID [PK]
      portfolio_id: UUID [FK]
      symbol: Symbol
      side: OrderSide
      quantity: Quantity
      avg_entry_price: Price
      current_price: Price
      unrealized_pnl: Price
      realized_pnl: Price
      opened_at: UTCDateTime
      updated_at: UTCDateTime

  - Balance
    fields:
      id: UUID [PK]
      portfolio_id: UUID [FK]
      currency: Currency
      total: Price
      available: Price
      locked: Price
      updated_at: UTCDateTime

  - AssetAllocation
    fields:
      symbol: Symbol
      quantity: Quantity
      current_value: Price
      allocation_percent: Decimal (0-100)
      target_percent: Decimal | None

value_objects:
  - PnL: Decimal (signed, represents profit or loss)
  - AllocationPercent: Decimal (0-100, validated)
  - RiskMetric: Decimal (various calculations)

domain_services:
  - PortfolioValuationService
    + calculate_total_value(portfolio: Portfolio, prices: dict) -> Price
    + calculate_unrealized_pnl(position: Position, current_price: Price) -> PnL
    + calculate_realized_pnl(trades: list[Trade]) -> PnL

  - AllocationService
    + calculate_current_allocation(portfolio: Portfolio) -> list[AssetAllocation]
    + detect_drift(portfolio: Portfolio) -> list[AllocationDrift]

  - RiskCalculationService
    + calculate_drawdown(equity_curve: list[EquityPoint]) -> DrawdownMetrics
    + calculate_sharpe_ratio(returns: list[Decimal]) -> Decimal
    + calculate_var(returns: list[Decimal], confidence: Decimal) -> Price

repositories:
  - PortfolioRepository (interface)
    + save(portfolio: Portfolio) -> None
    + get_active() -> Portfolio
    + get_by_id(id: UUID) -> Portfolio | None

  - PositionRepository (interface)
    + find_open_by_symbol(symbol: Symbol) -> Position | None
    + find_open_positions(portfolio_id: UUID) -> list[Position]
    + save(position: Position) -> None

domain_events:
  - PositionOpened { position: Position }
  - PositionClosed { position: Position, pnl: PnL }
  - PositionUpdated { position: Position }
  - BalanceChanged { balance: Balance, delta: Price }
  - PortfolioValueUpdated { portfolio_id: UUID, value: Price }
```

## 4. Analysis Module

**Bounded Context**: AI-powered market analysis and signal generation

```yaml
border: analysis
responsibility: >
  Leverage AI models for market analysis, pattern recognition, sentiment analysis,
  and signal generation. Provide explainable reasoning for all recommendations.

aggregates:
  - AnalysisAggregate
    root: Analysis
    members:
      - Signal
      - Reasoning
      - Confidence
      - SupportingEvidence

entities:
  - Analysis
    fields:
      id: UUID [PK]
      symbol: Symbol
      analysis_type: str  # technical, fundamental, sentiment
      result: str  # BUY, SELL, HOLD
      confidence: Decimal (0-1)
      reasoning: str
      model_used: str
      created_at: UTCDateTime
      expires_at: UTCDateTime

  - Signal
    fields:
      id: UUID [PK]
      analysis_id: UUID [FK]
      symbol: Symbol
      direction: OrderSide
      strength: Literal[WEAK, MODERATE, STRONG]
      entry_price: Price | None
      target_price: Price | None
      stop_loss: Price | None
      timeframe: Timeframe
      created_at: UTCDateTime
      valid_until: UTCDateTime

value_objects:
  - ConfidenceScore: Decimal (0-1, rounded to 2 decimals)
  - SignalStrength: Literal[WEAK, MODERATE, STRONG]

domain_services:
  - MarketAnalysisService
    + analyze_market(symbol: Symbol, timeframe: Timeframe) -> Analysis
    + detect_patterns(candles: list[Candle]) -> list[Pattern]
    + analyze_sentiment(news: list[str]) -> SentimentScore

  - SignalGenerationService
    + generate_signals(analysis: Analysis, risk_context: RiskContext) -> list[Signal]
    + rank_signals(signals: list[Signal]) -> list[Signal]
    + filter_by_confidence(signals: list[Signal], min_confidence: Decimal) -> list[Signal]

repositories:
  - AnalysisRepository (interface)
    + save(analysis: Analysis) -> None
    + find_recent(symbol: Symbol, limit) -> list[Analysis]
    + find_by_symbol(symbol: Symbol, start, end) -> list[Analysis]

  - SignalRepository (interface)
    + save(signal: Signal) -> None
    + find_active(symbol: Symbol | None) -> list[Signal]

domain_events:
  - AnalysisCompleted { analysis: Analysis }
  - SignalGenerated { signal: Signal }
  - PatternDetected { pattern: Pattern }
  - SignalExpired { signal: Signal }
```

## 5. Risk Module

**Bounded Context**: Risk management and compliance

```yaml
border: risk
responsibility: >
  Monitor position sizes, portfolio risk metrics, and enforce risk limits.
  Generate alerts when thresholds are breached.

aggregates:
  - RiskProfileAggregate
    root: RiskProfile
    members:
      - RiskLimit
      - RiskMetric
      - AlertThreshold

entities:
  - RiskProfile
    fields:
      id: UUID [PK]
      name: str
      max_position_size: Price
      max_portfolio_risk: Decimal (0-1)
      max_drawdown_percent: Decimal
      max_leverage: Decimal
      is_active: bool

  - RiskLimit
    fields:
      id: UUID [PK]
      profile_id: UUID [FK]
      limit_type: str  # position, portfolio, drawdown
      threshold: Decimal
      action: Literal[WARN, BLOCK, LIQUIDATE]
      is_active: bool

  - RiskAlert
    fields:
      id: UUID [PK]
      profile_id: UUID [FK]
      alert_type: str
      severity: Literal[LOW, MEDIUM, HIGH, CRITICAL]
      message: str
      data: dict
      acknowledged: bool
      created_at: UTCDateTime

domain_services:
  - RiskAssessmentService
    + assess_order_risk(order: Order, portfolio: Portfolio) -> RiskAssessment
    + assess_portfolio_risk(portfolio: Portfolio) -> PortfolioRiskReport
    + calculate_var_1d(positions: list[Position]) -> Price

  - RiskMonitoringService
    + check_limits(portfolio: Portfolio, market_data: MarketData) -> list[RiskAlert]
    + evaluate_thresholds(metric: Decimal, threshold: Decimal) -> bool

repositories:
  - RiskProfileRepository (interface)
    + get_active() -> RiskProfile
    + save(profile: RiskProfile) -> None

  - RiskAlertRepository (interface)
    + save(alert: RiskAlert) -> None
    + find_unacknowledged() -> list[RiskAlert]
    + acknowledge(id: UUID) -> None

domain_events:
  - RiskLimitApproaching { alert: RiskAlert }
  - RiskLimitBreached { alert: RiskAlert }
  - RiskThresholdRestored { alert: RiskAlert }
```

## 6. Domain Event Flow Examples

### 6.1 Trade Execution Flow
```
OrderCreated
  → OrderOpened
    → MarketTickReceived (price update)
      → OrderMatched
        → TradeExecuted
          → PositionUpdated
            → PortfolioValueUpdated
              → RiskCheckPerformed
                → (if breach) RiskLimitBreached
```

### 6.2 AI Analysis Flow
```
MarketTickReceived
  → CandleCompleted (when timeframe closes)
    → SignalGenerated
      → OrderPlaced (if risk allows)
        → (trade loop repeats)
```

## 7. Anti-Corruption Layers

Each bounded context protects its domain from external changes:

```
External System (CCXT) → Adapter → Normalized Domain Model
External AI API → Adapter → Analysis Domain Model
Telegram API → Gateway → Command/Query → Application Layer
```

**Adapters Location**: `src/infrastructure/exchanges/`, `src/infrastructure/ai/`

## 8. Module Communication Matrix

| Source Module | Target Module | Communication Type | Events/Data |
|--------------|--------------|-------------------|-------------|
| trading | portfolio | Domain event | TradeExecuted → PositionUpdated |
| trading | risk | Domain event | OrderPlaced → RiskAssessmentRequested |
| market_data | trading | Event | CandleCompleted → CheckStrategy |
| analysis | trading | Command | SignalGenerated → PlaceOrder |
| portfolio | notification | Event | PortfolioValueUpdated → ReportGenerated |
| risk | notification | Event | RiskLimitBreached → AlertUser |
