# Module Architecture

## Domain Modules (Bounded Contexts)

### Trading Module
- Entities: Order, Trade, Position
- Services: OrderExecutor, TradeMatcher, PositionManager
- Events: OrderPlaced, OrderFilled, TradeExecuted, PositionOpened, PositionClosed
- Responsibilities: Order lifecycle management, execution coordination

### Market Data Module
- Entities: MarketData, Symbol, OHLCV, Ticker
- Services: DataAggregator, PriceCalculator, DataNormalizer
- Events: PriceUpdated, DataReceived, SymbolAdded
- Responsibilities: Data ingestion, normalization, caching coordination

### Portfolio Module
- Entities: Portfolio, Asset, Balance, Snapshot
- Services: PortfolioCalculator, BalanceUpdater, PerformanceAnalyzer
- Events: PortfolioUpdated, AssetAdded, SnapshotCreated
- Responsibilities: Position tracking, balance management, performance calculation

### Risk Module
- Entities: RiskConfig, RiskLimit, RiskAlert, Exposure
- Services: RiskEvaluator, LimitChecker, ExposureCalculator
- Events: RiskTriggered, LimitExceeded, ExposureUpdated
- Responsibilities: Risk limit enforcement, exposure monitoring, alert generation

### AI/Strategy Module
- Entities: Strategy, Signal, Analysis, BacktestResult
- Services: StrategyGenerator, SignalProcessor, BacktestEngine
- Events: StrategyGenerated, SignalCreated, BacktestCompleted
- Responsibilities: AI strategy generation, signal processing, backtest orchestration

### User Module
- Entities: User, Preferences, ApiKey, Session
- Services: UserManager, KeyValidator, PreferenceManager
- Events: UserUpdated, KeyRotated, PreferencesChanged
- Responsibilities: Single-user management, API key rotation, preferences

### Notification Module
- Entities: Notification, Alert, MessageTemplate
- Services: NotificationDispatcher, AlertProcessor, TemplateRenderer
- Events: NotificationSent, AlertTriggered, DeliveryFailed
- Responsibilities: Notification routing, template management, delivery tracking

## Module Boundaries

Trading, Market Data, and Portfolio modules interact through domain events. Risk Module validates all trading actions. AI/Strategy Module generates signals that trigger Trading. Notification Module handles all user-facing alerts.

## Shared Kernel

Types shared across all modules:
- Money: Precise monetary calculations
- Symbol: Exchange symbol normalization
- Timestamp: Consistent UTC time handling
- OrderSide / OrderType: Enums for trading operations
- RiskLevel: Common risk categorization
- BaseEntity: Common entity attributes (id, created_at, updated_at)

## Anti-Corruption Layers

- Exchange Adapter: Translates CCXT types to domain types
- AI Provider Adapter: Normalizes different AI API responses
- Telegram Adapter: Maps Telegram update types to domain commands

## Event-Driven Communication

All inter-module communication uses domain events:
1. Domain entity raises event after state change
2. Event published to EventBus
3. Handlers in other modules react to events
4. No direct module-to-module calls
