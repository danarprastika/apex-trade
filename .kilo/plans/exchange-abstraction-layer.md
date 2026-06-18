# APEX Exchange Abstraction Layer Plan

Version: 0.1  
Status: Draft Plan  
Date: 2026-06-16  
Scope: Exchange integration architecture for Binance, Bybit, OKX, KuCoin, Kraken, and Interactive Brokers.

---

## Current Architecture Summary

APEX currently has a functional but Binance-centric exchange integration foundation.

### Existing Exchange-Related Files

| Area | Existing File | Current Role |
|---|---|---|
| Binance integration | `backend/app/integrations/binance/client.py` | CCXT-based Binance client for OHLCV candles and ticker data. |
| Exchange service | `backend/app/services/exchange_service.py` | Exchange/account CRUD, credential encryption, connection test, account sync. |
| Exchange DB model | `backend/app/database/models/exchange.py` | Stores exchange metadata and encrypted account credentials. |
| Exchange repository | `backend/app/database/repositories/exchange_repository.py` | Basic exchange/account lookup. |
| Exchange API routes | `backend/app/api/v1/exchanges/routes.py` | Create/list exchanges, create/list accounts, test connection, sync account. |
| Market collector | `backend/app/tasks/collectors/market_collector.py` | Scheduled Binance testnet candle collection and persistence. |
| Trading models | `backend/app/database/models/trading.py` | Internal order, position, trade, signal, and strategy records. |
| Market models | `backend/app/database/models/market.py` | Assets, market pairs, candles, order book snapshots, funding rates, open interest. |
| Portfolio models | `backend/app/database/models/portfolio.py` | Portfolio, allocations, and snapshots. |

### Current Architecture Assessment

The current implementation is suitable as a single-exchange MVP foundation, but it is not ready for multi-exchange production use. The Binance client is directly imported by the market collector, `ExchangeService` builds CCXT clients dynamically from `exchange_type`, and there is no formal exchange interface, adapter registry, capability model, unified order lifecycle, unified position model, rate-limit policy, retry policy, or failover strategy.

---

# 1. Gap Analysis

## 1.1 Exchange Interface Gap

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
| No formal exchange interface | Only `BinanceClient` exists under `integrations/binance`. | Every new exchange requires custom wiring and risks inconsistent behavior. | Critical |
| No adapter registry | `ExchangeService` dynamically resolves CCXT classes from `exchange_type`. | Hard to validate capabilities, enforce constraints, or swap providers. | Critical |
| No capability model | `Exchange` model only stores `name`, `exchange_type`, and `status`. | Cannot know which exchanges support spot, margin, futures, stocks, symbols, order types, or order book data. | Critical |
| No adapter factory | Market collector imports `BinanceClient` directly. | Tightly couples market data collection to Binance. | High |
| No exchange abstraction for IBKR | Current design assumes crypto exchange behavior. | Interactive Brokers has different instruments, accounts, orders, and execution semantics. | High |

## 1.2 Unified Model Gap

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
| Market data is partially unified | `Candle`, `OrderBookSnapshot`, `FundingRate`, and `OpenInterestRecord` exist, but no unified ticker/order book abstraction. | Multi-exchange market data normalization is incomplete. | High |
| Order model is internal-only | `Order` stores local fields but lacks client order ID, idempotency key, raw status, fees, timestamps, rejection reasons, and reconciliation state. | Live order lifecycle cannot be safely reconciled across exchanges. | Critical |
| Position model is internal-only | `Position` lacks exchange position ID, mark price, leverage, margin, liquidation price, realized PnL, and raw payload. | Multi-exchange position tracking will be inaccurate. | Critical |
| No unified balance model | `ExchangeAccount.balance_snapshot` stores raw JSON only. | Portfolio valuation and exposure checks cannot rely on normalized balances. | High |
| No unified error model | Exceptions are mostly generic or validation-based. | Retry, alerting, and failover decisions cannot be automated reliably. | High |

## 1.3 Rate Limit Handling Gap

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
| Rate limiting is delegated to CCXT only | `BinanceClient` and `ExchangeService` set `enableRateLimit=True`. | No APEX-level visibility, metrics, or adaptive throttling. | High |
| No per-exchange rate-limit policy | No rate-limit config exists. | Exchanges with different limits can be overloaded. | High |
| No endpoint-level throttling | No endpoint-specific policy for market data, account sync, orders, or positions. | High-frequency market collection and order sync can conflict. | High |
| No retry-after handling | No explicit handling of exchange rate-limit responses. | Retries may worsen rate-limit failures. | Medium |

## 1.4 Retry Logic Gap

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
| No retry policy | Market collector catches and logs failures but does not retry. | Temporary exchange/network failures cause missed data. | High |
| No retry classification | No distinction between transient, permanent, and unknown errors. | Unsafe retries can create duplicate orders or inconsistent state. | Critical |
| No idempotency for order submission | `ExecutionService.create_order` creates DB records only. | Future live order submission must avoid duplicate execution. | Critical |
| No retry budget | No max retry count, backoff, or dead-letter handling. | Failed operations can loop indefinitely or disappear silently. | High |

## 1.5 Error Handling Gap

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
| Generic exception handling | `ExchangeService` often catches broad exceptions and wraps them as `ValidationError`. | Operators cannot distinguish credential, network, rate-limit, or exchange-side failures. | High |
| No exchange error taxonomy | No structured error categories exist. | Retry, alerting, and failover cannot be policy-driven. | High |
| Raw exception messages stored | `ExchangeAccount.error_message` stores raw exception text. | Sensitive or noisy data may be persisted. | Medium |
| No structured exchange logs | Logs are basic and not correlated to exchange/account/request. | Incident investigation is harder. | Medium |

## 1.6 Failover Strategy Gap

| Gap | Evidence | Impact | Priority |
|---|---|---|---|
| No failover strategy | Only Binance integration exists. | No guidance for market data or order execution failover. | Critical |
| No exchange health model | No exchange status, latency, error rate, or capability health tracking. | Cannot decide when to fail over. | High |
| No market data fallback | Market collector hardcodes Binance testnet. | Market data collection stops if Binance is unavailable. | High |
| No order routing policy | No routing rules for choosing exchange/account. | Future multi-exchange trading could submit orders to unintended venues. | Critical |
| No reconciliation after failover | No reconciliation workflow exists. | Failed or partially submitted orders may diverge between APEX and exchange state. | Critical |

---

# 2. Missing Components

## 2.1 Core Missing Components

| Component | Purpose | Priority |
|---|---|---|
| Exchange interface | Defines the contract all exchange adapters must implement. | Critical |
| Exchange adapter registry | Maps exchange IDs/names to concrete adapters. | Critical |
| Exchange factory | Creates adapters with credentials, environment, and configuration. | Critical |
| Exchange capability model | Describes supported markets, instruments, order types, data feeds, and limitations. | Critical |
| Unified market data model | Normalizes candles, tickers, order books, funding rates, and open interest. | Critical |
| Unified order model | Normalizes local and exchange order state across all exchanges. | Critical |
| Unified position model | Normalizes exchange positions, leverage, margin, PnL, and mark prices. | Critical |
| Unified balance model | Normalizes free, used, total, currency, and account balances. | High |
| Exchange error taxonomy | Classifies errors for retry, alerting, and failover decisions. | Critical |
| Rate-limit manager | Enforces per-exchange and endpoint-level request limits. | High |
| Retry manager | Applies safe retry policies with backoff and retry budgets. | Critical |
| Circuit breaker | Prevents cascading failures when an exchange is unhealthy. | High |
| Exchange health tracker | Tracks latency, success rate, error rate, and availability. | High |
| Failover policy engine | Decides when to switch market data or execution routes. | Critical |
| Order idempotency manager | Prevents duplicate live orders during retries or failover. | Critical |
| Reconciliation service | Compares local APEX orders/positions with exchange state. | Critical |

## 2.2 Exchange-Specific Missing Components

| Exchange | Missing Adapter Needs | Priority |
|---|---|---|
| Binance | Refactor existing Binance client into adapter, add order book, ticker, balance, position, order submit/cancel/status, sandbox handling. | Critical |
| Bybit | Add spot/linear derivatives support, symbol normalization, rate-limit rules, order lifecycle mapping. | High |
| OKX | Add instrument families, account mode handling, order state mapping, rate-limit rules. | High |
| KuCoin | Add public/private API support, symbol normalization, order lifecycle mapping. | Medium |
| Kraken | Add asset pair normalization, order state mapping, account balance/position mapping. | Medium |
| Interactive Brokers | Add broker-specific account, contract, order, execution, and portfolio abstractions. | Medium |

## 2.3 Operational Missing Components

| Component | Purpose | Priority |
|---|---|---|
| Exchange metrics | Track API calls, latency, errors, retries, rate limits, and health. | High |
| Exchange dashboards | Show exchange availability, adapter health, order status, and reconciliation gaps. | High |
| Exchange alerting | Alert on repeated failures, rate-limit saturation, reconciliation drift, and failover events. | High |
| Exchange adapter tests | Unit, contract, and integration tests for each adapter. | Critical |
| Mock exchange client | Deterministic testing without live exchange dependencies. | Critical |
| Adapter documentation | Required fields, supported features, limitations, and known differences. | High |

---

# 3. Recommended Folder Structure

## 3.1 Recommended Backend Structure

```text
backend/app/
├── domain/
│   └── exchange/
│       ├── entities/
│       │   ├── Exchange.py
│       │   ├── ExchangeAccount.py
│       │   ├── ExchangeCapability.py
│       │   ├── ExchangeHealth.py
│       │   ├── MarketData.py
│       │   ├── Order.py
│       │   ├── Position.py
│       │   └── Balance.py
│       ├── value_objects/
│       │   ├── Symbol.py
│       │   ├── Money.py
│       │   ├── Quantity.py
│       │   ├── Side.py
│       │   ├── OrderType.py
│       │   ├── TimeInForce.py
│       │   └── ExchangeErrorCategory.py
│       └── events/
│           ├── ExchangeConnected.py
│           ├── ExchangeDisconnected.py
│           ├── OrderSubmitted.py
│           ├── OrderUpdated.py
│           ├── PositionUpdated.py
│           └── ExchangeFailoverTriggered.py
│
├── services/
│   ├── exchange/
│   │   ├── ExchangeService.py
│   │   ├── ExchangeAccountService.py
│   │   ├── ExchangeCapabilityService.py
│   │   ├── ExchangeHealthService.py
│   │   ├── ExchangeReconciliationService.py
│   │   └── ExchangeFailoverService.py
│   └── execution/
│       ├── OrderRoutingService.py
│       ├── OrderLifecycleService.py
│       └── OrderIdempotencyService.py
│
├── integrations/
│   └── exchanges/
│       ├── interfaces/
│       │   ├── ExchangeAdapter.py
│       │   ├── MarketDataAdapter.py
│       │   ├── OrderAdapter.py
│       │   └── PositionAdapter.py
│       ├── base/
│       │   ├── BaseExchangeAdapter.py
│       │   ├── BaseRateLimitManager.py
│       │   ├── BaseRetryManager.py
│       │   ├── BaseCircuitBreaker.py
│       │   ├── ExchangeError.py
│       │   └── ExchangeOperationContext.py
│       ├── registry/
│       │   ├── ExchangeAdapterRegistry.py
│       │   ├── ExchangeAdapterFactory.py
│       │   └── ExchangeCapabilityCatalog.py
│       ├── rate_limit/
│       │   ├── RateLimitPolicy.py
│       │   ├── TokenBucketRateLimiter.py
│       │   └── ExchangeRateLimitManager.py
│       ├── retry/
│       │   ├── RetryPolicy.py
│       │   ├── RetryManager.py
│       │   └── RetryDecision.py
│       ├── failover/
│       │   ├── FailoverPolicy.py
│       │   ├── FailoverDecision.py
│       │   └── ExchangeFailoverManager.py
│       ├── errors/
│       │   ├── ExchangeErrorTaxonomy.py
│       │   ├── ExchangeErrorMapper.py
│       │   └── ExchangeException.py
│       ├── binance/
│       │   ├── BinanceAdapter.py
│       │   ├── BinanceMarketDataAdapter.py
│       │   ├── BinanceOrderAdapter.py
│       │   ├── BinancePositionAdapter.py
│       │   ├── BinanceRateLimitPolicy.py
│       │   └── BinanceErrorMapper.py
│       ├── bybit/
│       │   ├── BybitAdapter.py
│       │   ├── BybitMarketDataAdapter.py
│       │   ├── BybitOrderAdapter.py
│       │   ├── BybitPositionAdapter.py
│       │   ├── BybitRateLimitPolicy.py
│       │   └── BybitErrorMapper.py
│       ├── okx/
│       │   ├── OkxAdapter.py
│       │   ├── OkxMarketDataAdapter.py
│       │   ├── OkxOrderAdapter.py
│       │   ├── OkxPositionAdapter.py
│       │   ├── OkxRateLimitPolicy.py
│       │   └── OkxErrorMapper.py
│       ├── kucoin/
│       │   ├── KuCoinAdapter.py
│       │   ├── KuCoinMarketDataAdapter.py
│       │   ├── KuCoinOrderAdapter.py
│       │   ├── KuCoinPositionAdapter.py
│       │   ├── KuCoinRateLimitPolicy.py
│       │   └── KuCoinErrorMapper.py
│       ├── kraken/
│       │   ├── KrakenAdapter.py
│       │   ├── KrakenMarketDataAdapter.py
│       │   ├── KrakenOrderAdapter.py
│       │   ├── KrakenPositionAdapter.py
│       │   ├── KrakenRateLimitPolicy.py
│       │   └── KrakenErrorMapper.py
│       └── interactive_brokers/
│           ├── InteractiveBrokersAdapter.py
│           ├── InteractiveBrokersMarketDataAdapter.py
│           ├── InteractiveBrokersOrderAdapter.py
│           ├── InteractiveBrokersPositionAdapter.py
│           ├── InteractiveBrokersRateLimitPolicy.py
│           └── InteractiveBrokersErrorMapper.py
│
├── schemas/
│   └── exchange/
│       ├── ExchangeCapabilityRead.py
│       ├── ExchangeHealthRead.py
│       ├── UnifiedTickerRead.py
│       ├── UnifiedCandleRead.py
│       ├── UnifiedOrderBookRead.py
│       ├── UnifiedOrderRead.py
│       ├── UnifiedPositionRead.py
│       └── UnifiedBalanceRead.py
│
└── tasks/
    └── collectors/
        ├── market_data_collector.py
        ├── exchange_account_sync_collector.py
        └── exchange_reconciliation_collector.py
```

## 3.2 Why This Structure

| Folder | Reason |
|---|---|
| `domain/exchange` | Owns pure business concepts and value objects. |
| `services/exchange` | Coordinates account management, capability checks, health, reconciliation, and failover. |
| `services/execution` | Owns order routing and lifecycle logic independent from exchange-specific APIs. |
| `integrations/exchanges` | Contains all external exchange adapters and cross-cutting exchange infrastructure. |
| `interfaces` | Defines contracts so adapters remain interchangeable. |
| `base` | Provides shared retry, rate-limit, error, and circuit-breaker behavior. |
| `registry` | Centralizes adapter discovery and capability lookup. |
| Exchange-specific folders | Keep vendor-specific code isolated and replaceable. |
| `schemas/exchange` | Exposes unified DTOs to API consumers without leaking vendor payloads. |

---

# 4. Interface Definitions

## 4.1 Exchange Interface

The exchange interface should define the minimum contract required by APEX for every supported exchange.

| Operation Group | Required Methods | Purpose |
|---|---|---|
| Metadata | `get_exchange_info`, `get_capabilities`, `get_supported_symbols`, `get_supported_timeframes` | Discover supported markets and features. |
| Market data | `fetch_candles`, `fetch_ticker`, `fetch_order_book`, `fetch_funding_rate`, `fetch_open_interest` | Retrieve normalized market data. |
| Account | `test_connection`, `fetch_balances`, `fetch_positions` | Validate credentials and sync account state. |
| Orders | `submit_order`, `cancel_order`, `modify_order`, `fetch_order`, `fetch_open_orders` | Manage order lifecycle safely. |
| Health | `get_exchange_status`, `get_latency`, `get_rate_limit_state` | Support monitoring, retry, and failover. |
| Normalization | `normalize_symbol`, `denormalize_symbol`, `map_order_status`, `map_error` | Convert between APEX and vendor models. |

## 4.2 Exchange Adapter Pattern

Each exchange should be implemented as an adapter that translates between APEX domain models and vendor-specific APIs.

| Adapter Layer | Responsibility |
|---|---|
| Vendor client wrapper | Owns raw SDK/API calls and vendor-specific configuration. |
| Market data adapter | Converts candles, tickers, order books, funding, and open interest into unified models. |
| Order adapter | Converts APEX order requests to vendor orders and vendor responses to unified orders. |
| Position adapter | Converts vendor positions to unified positions. |
| Error mapper | Maps vendor errors to APEX exchange error categories. |
| Rate-limit policy | Defines endpoint limits and throttle behavior. |
| Retry policy | Defines safe retry behavior for each operation. |
| Capability profile | Describes what the exchange supports and what it does not. |

## 4.3 Unified Market Data Model

| Field Group | Fields |
|---|---|
| Identity | `exchange_id`, `exchange_name`, `adapter_name`, `source_symbol`, `normalized_symbol`, `base_asset`, `quote_asset`, `asset_class` |
| Candle | `timeframe`, `open_time`, `close_time`, `open`, `high`, `low`, `close`, `volume`, `quote_volume`, `trade_count` |
| Ticker | `last_price`, `bid_price`, `ask_price`, `bid_size`, `ask_size`, `high_24h`, `low_24h`, `volume_24h`, `price_change_24h` |
| Order book | `bids`, `asks`, `spread`, `spread_percentage`, `best_bid`, `best_ask`, `depth_level`, `captured_at` |
| Derivatives | `funding_rate`, `next_funding_time`, `open_interest`, `mark_price`, `index_price` |
| Quality | `data_quality_score`, `is_stale`, `source_timestamp`, `received_at`, `normalization_version` |

## 4.4 Unified Order Model

| Field Group | Fields |
|---|---|
| Identity | `internal_order_id`, `idempotency_key`, `client_order_id`, `exchange_order_id`, `user_id`, `exchange_account_id`, `exchange_id` |
| Routing | `strategy_id`, `signal_id`, `execution_source`, `routing_decision_id`, `failover_attempt`, `primary_exchange_id`, `fallback_exchange_id` |
| Instrument | `source_symbol`, `normalized_symbol`, `base_asset`, `quote_asset`, `asset_class` |
| Order intent | `side`, `order_type`, `time_in_force`, `quantity`, `quote_quantity`, `price`, `trigger_price`, `stop_loss`, `take_profit` |
| Execution state | `status`, `raw_status`, `filled_quantity`, `remaining_quantity`, `average_price`, `last_fill_price`, `last_fill_time` |
| Fees and costs | `fee_currency`, `fee_amount`, `commission`, `slippage`, `notional_value` |
| Timestamps | `created_at`, `submitted_at`, `accepted_at`, `filled_at`, `cancelled_at`, `updated_at` |
| Reconciliation | `reconciliation_status`, `last_synced_at`, `last_reconciliation_error`, `raw_payload_hash` |
| Safety | `risk_decision_id`, `pre_trade_check_id`, `kill_switch_checked_at`, `duplicate_check_id` |

## 4.5 Unified Position Model

| Field Group | Fields |
|---|---|
| Identity | `internal_position_id`, `exchange_position_id`, `user_id`, `exchange_account_id`, `exchange_id` |
| Instrument | `source_symbol`, `normalized_symbol`, `base_asset`, `quote_asset`, `asset_class` |
| State | `side`, `quantity`, `entry_price`, `current_price`, `mark_price`, `liquidation_price` |
| PnL | `unrealized_pnl`, `realized_pnl`, `daily_pnl`, `total_pnl`, `pnl_currency` |
| Margin | `leverage`, `margin_used`, `maintenance_margin`, `notional_value`, `margin_ratio` |
| Lifecycle | `opened_at`, `updated_at`, `closed_at`, `status` |
| Reconciliation | `last_synced_at`, `reconciliation_status`, `raw_payload_hash` |

## 4.6 Unified Balance Model

| Field Group | Fields |
|---|---|
| Identity | `exchange_account_id`, `exchange_id`, `user_id`, `currency`, `asset_class` |
| Balance | `free`, `used`, `total`, `available`, `locked`, `borrowed` |
| Valuation | `last_price`, `valuation_currency`, `estimated_value` |
| Timestamps | `captured_at`, `last_synced_at` |
| Reconciliation | `reconciliation_status`, `raw_payload_hash` |

## 4.7 Rate Limit Handling

| Component | Requirement |
|---|---|
| Per-exchange policy | Each adapter must declare rate limits by endpoint and operation type. |
| Token bucket | Use token bucket behavior for burst control. |
| Endpoint separation | Public market data, private account, and order endpoints must be throttled separately. |
| Retry-after awareness | Respect exchange-provided retry-after headers or messages. |
| Adaptive throttling | Increase delay when repeated rate-limit errors occur. |
| Metrics | Emit request count, throttled count, retry-after count, and latency per exchange. |
| Safety | Rate limiting must never be bypassed for order submission or account sync. |

## 4.8 Retry Logic

| Requirement | Description |
|---|---|
| Retry classification | Classify errors as retryable, non-retryable, or unknown. |
| Safe retry | Market data, balance, position, and order status can be retried safely. |
| Idempotent order retry | Order submission retry is allowed only with a stable client order ID or idempotency key. |
| Backoff | Use exponential backoff with jitter. |
| Retry budget | Define max attempts per operation and operation type. |
| Dead-letter path | Failed durable operations should move to a retry queue or DLQ. |
| Unknown order state | If order submission result is unknown, do not blindly retry; reconcile first. |
| Circuit breaker | Stop retrying a failing exchange when circuit breaker opens. |

## 4.9 Error Handling

| Error Category | Examples | Retry Behavior |
|---|---|---|
| Configuration error | Missing API key, unsupported exchange, invalid adapter config | No retry. |
| Credential error | Invalid API key, insufficient permissions, expired token | No retry until credentials are fixed. |
| Validation error | Invalid symbol, invalid quantity, unsupported order type | No retry. |
| Rate-limit error | 429, too many requests, retry-after | Retry after throttling. |
| Network error | Timeout, DNS failure, connection reset | Retry with backoff. |
| Temporary exchange error | 500, 502, 503, maintenance | Retry with circuit breaker. |
| Unknown order state | Submitted but response lost | Reconcile before retry. |
| Reconciliation error | Local and exchange state mismatch | Alert and pause affected workflow. |
| Failover error | Fallback exchange unavailable or unsupported | Escalate to manual review. |

## 4.10 Failover Strategy

| Failover Area | Strategy |
|---|---|
| Market data | If primary exchange market data fails, read from secondary exchange only if symbol mapping and data quality are acceptable. |
| Account sync | Retry on same exchange first. Do not fail over to another exchange for account state. |
| Order execution | Failover only if strategy explicitly supports multi-exchange routing and the order is not already submitted. |
| Unknown order state | Never submit a replacement order until reconciliation confirms no existing order/fill exists. |
| Exchange health | Use latency, error rate, rate-limit saturation, and circuit breaker state to determine health. |
| Manual override | High-impact failover decisions should require human approval until policy is mature. |
| Audit | Every failover decision must record primary exchange, fallback exchange, reason, timestamp, and operator/system actor. |

---

# 5. Scalability Strategy

## 5.1 Adapter Scalability

| Concern | Strategy |
|---|---|
| Adding new exchanges | Add adapter folder, capability profile, rate-limit policy, error mapper, and tests without changing core services. |
| Exchange-specific behavior | Keep vendor-specific code isolated inside adapter folders. |
| Shared behavior | Put retry, rate limiting, circuit breaking, and normalization helpers in base integration modules. |
| Capability discovery | Use capability catalog to avoid calling unsupported operations. |

## 5.2 Market Data Scalability

| Concern | Strategy |
|---|---|
| High-frequency candles | Use dedicated market data workers per exchange or asset class. |
| Many symbols | Partition collection jobs by exchange, asset class, and symbol group. |
| Real-time data | Add WebSocket/streaming adapters later; keep unified model stable. |
| Data volume | Partition `candles` and related time-series tables by exchange/timeframe/date. |
| Duplicate prevention | Enforce uniqueness on exchange ID, market pair ID, timeframe, and open time. |
| Cache | Cache symbols, assets, market pairs, and exchange metadata in Redis. |

## 5.3 Order Lifecycle Scalability

| Concern | Strategy |
|---|---|
| Order submission | Use idempotency keys and client order IDs. |
| Unknown state | Reconcile before retrying. |
| Multiple exchanges | Route through `OrderRoutingService`, not direct adapter calls. |
| High order volume | Use durable queue and worker pools per exchange. |
| Reconciliation | Schedule periodic reconciliation and event-driven reconciliation after order updates. |
| Safety | Kill switch and risk checks must gate all order routing. |

## 5.4 Reliability Scalability

| Concern | Strategy |
|---|---|
| Exchange outage | Circuit breaker and health tracker prevent cascading failures. |
| Rate limits | Endpoint-level rate limiters prevent abuse. |
| Failed jobs | Durable retry queue and DLQ preserve failed operations. |
| Monitoring | Metrics for latency, error rate, retries, rate limits, and reconciliation drift. |
| Alerting | Alerts for repeated failures, unknown order states, and reconciliation drift. |

## 5.5 Database Scalability

| Concern | Strategy |
|---|---|
| Market data volume | Partition time-series tables and add composite indexes. |
| Order history | Index by user, exchange account, exchange order ID, status, and created date. |
| Audit/reconciliation | Partition by date and user/exchange. |
| Read scaling | Add read replicas after write volume grows. |
| Hot metadata | Cache exchange metadata and symbol mappings. |

---

# 6. Migration Plan

## Phase 0: Preparation

**Goal:** Freeze current Binance behavior and prepare for abstraction.

### Tasks

- Inventory all current Binance usage.
- Identify all direct imports of `BinanceClient`.
- Identify all direct CCXT usage outside `ExchangeService`.
- Document current API behavior for exchange account create, test, and sync.
- Define adapter acceptance criteria.

### Acceptance Criteria

- All Binance dependencies are known.
- No hidden direct exchange calls remain undocumented.
- Current behavior is captured before refactor.

---

## Phase 1: Domain and Interface Design

**Goal:** Define exchange domain objects and contracts.

### Tasks

- Define exchange domain entities.
- Define unified market data, order, position, and balance models.
- Define exchange capability model.
- Define exchange error taxonomy.
- Define retry and rate-limit policy objects.
- Define failover policy objects.

### Acceptance Criteria

- Core exchange domain contracts are approved.
- Unified models cover Binance and future exchanges.
- IBKR-specific differences are represented without breaking crypto exchange models.

---

## Phase 2: Adapter Infrastructure

**Goal:** Build the shared adapter framework without changing behavior.

### Tasks

- Create exchange adapter interface.
- Create adapter registry.
- Create adapter factory.
- Create base adapter helpers.
- Create rate-limit manager.
- Create retry manager.
- Create circuit breaker.
- Create exchange error mapper.
- Create capability catalog.

### Acceptance Criteria

- Adapters can be registered and resolved by exchange ID.
- Shared retry, rate-limit, and error behavior is available.
- No production behavior changes yet.

---

## Phase 3: Binance Adapter Extraction

**Goal:** Move existing Binance behavior behind the adapter interface.

### Tasks

- Create Binance adapter.
- Move existing OHLCV and ticker behavior into Binance market data adapter.
- Add Binance account test and sync adapter behavior.
- Preserve existing API responses during migration.
- Update market collector to use adapter registry instead of direct Binance import.
- Keep old Binance client temporarily as compatibility wrapper if needed.

### Acceptance Criteria

- Market collector no longer imports Binance directly.
- Binance candle collection behavior remains unchanged.
- Exchange account test and sync continue to work.
- Binance adapter passes existing tests.

---

## Phase 4: Unified Order and Position Models

**Goal:** Prepare for live order lifecycle and reconciliation.

### Tasks

- Extend order model with idempotency, client order ID, raw status, timestamps, fees, and reconciliation fields.
- Extend position model with exchange position ID, mark price, leverage, margin, liquidation price, and realized PnL.
- Add unified balance model.
- Add reconciliation status fields.
- Add migration plan for existing data.

### Acceptance Criteria

- Existing order and position records can be mapped to unified models.
- New fields support reconciliation and multi-exchange behavior.
- Existing API responses remain backward compatible where possible.

---

## Phase 5: Retry, Rate Limit, and Error Handling Integration

**Goal:** Make exchange operations resilient and observable.

### Tasks

- Apply rate-limit manager to Binance adapter.
- Apply retry manager to market data and account sync operations.
- Apply safe retry rules to order-related operations.
- Map Binance errors into exchange error taxonomy.
- Add metrics for retries, rate limits, latency, and failures.
- Add structured logs with exchange/account/request context.

### Acceptance Criteria

- Rate-limit errors are handled without overwhelming Binance.
- Temporary failures retry safely.
- Non-retryable errors do not retry.
- Unknown order states trigger reconciliation instead of blind retry.

---

## Phase 6: Order Lifecycle Service

**Goal:** Centralize order routing and execution safety.

### Tasks

- Create order routing service.
- Create order lifecycle service.
- Create order idempotency service.
- Integrate risk checks before order submission.
- Integrate kill switch before order submission.
- Add client order ID/idempotency key generation.
- Add order status sync.
- Add order cancellation and modification preparation.

### Acceptance Criteria

- Orders are submitted through routing service, not direct adapters.
- Risk and kill switch gates are enforced.
- Duplicate order submissions are prevented.
- Order status can be synced from exchange.

---

## Phase 7: Reconciliation and Failover

**Goal:** Add production-grade safety for exchange state divergence.

### Tasks

- Add reconciliation service for orders, positions, and balances.
- Add unknown order state workflow.
- Add exchange health tracker.
- Add failover policy engine.
- Add market data fallback rules.
- Add failover audit logging.
- Add alerts for reconciliation drift.

### Acceptance Criteria

- Local orders can be reconciled with exchange orders.
- Positions can be reconciled with exchange positions.
- Market data can fail over safely when configured.
- Order execution failover is blocked unless explicitly supported.
- Reconciliation drift generates alerts.

---

## Phase 8: Bybit and OKX Adapters

**Goal:** Add the first multi-exchange production candidates.

### Tasks

- Add Bybit capability profile.
- Add Bybit symbol normalization.
- Add Bybit market data adapter.
- Add Bybit account/order/position adapter.
- Add Bybit rate-limit and error mapping.
- Add OKX capability profile.
- Add OKX symbol normalization.
- Add OKX market data adapter.
- Add OKX account/order/position adapter.
- Add OKX rate-limit and error mapping.

### Acceptance Criteria

- Bybit and OKX can be registered through adapter registry.
- Market data collection works through unified models.
- Account test/sync works through unified models.
- Unsupported features fail clearly instead of behaving unpredictably.

---

## Phase 9: KuCoin, Kraken, and Interactive Brokers

**Goal:** Expand adapter coverage while preserving stable core contracts.

### Tasks

- Add KuCoin adapter.
- Add Kraken adapter.
- Add Interactive Brokers adapter.
- Add IBKR contract/instrument mapping.
- Add IBKR account and execution mapping.
- Add broker-specific rate-limit policies.
- Add broker-specific error mapping.
- Add exchange-specific capability flags.

### Acceptance Criteria

- Each exchange can be enabled or disabled through configuration.
- Unsupported features are clearly reported.
- IBKR does not share unsafe assumptions with crypto spot/futures exchanges.
- Adapter tests cover each exchange's core behavior.

---

## Phase 10: Decommission Legacy Direct Exchange Code

**Goal:** Remove tight coupling and finalize abstraction.

### Tasks

- Remove direct `BinanceClient` imports from collectors.
- Remove direct CCXT usage from services.
- Keep compatibility wrappers only if necessary.
- Update docs and API contracts.
- Remove obsolete exchange-specific assumptions.
- Finalize migration guide.

### Acceptance Criteria

- Core services depend on exchange interfaces, not concrete exchange clients.
- New exchange onboarding requires only adapter implementation and configuration.
- Legacy direct exchange code is removed or clearly marked deprecated.

---

# Migration Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Binance behavior changes during refactor | Preserve API responses and add compatibility tests before migration. |
| Duplicate live orders during retry | Use idempotency keys, client order IDs, and unknown-state reconciliation. |
| Exchange-specific assumptions leak into core | Keep vendor logic inside adapter folders. |
| IBKR does not fit crypto model | Extend unified models with asset class and contract fields instead of forcing crypto assumptions. |
| Rate limits cause missed market data | Use endpoint-level throttling, priority queues, and data freshness alerts. |
| Failover creates inconsistent state | Restrict order execution failover and audit every failover decision. |
| Raw exchange errors expose sensitive data | Map errors to sanitized taxonomy before storage or API response. |

---

# Recommended Implementation Order

1. Define interfaces, unified models, and capability model.
2. Build adapter registry, factory, retry, rate-limit, and error infrastructure.
3. Extract Binance into the adapter pattern.
4. Add order idempotency and reconciliation foundations.
5. Add exchange health and failover policy.
6. Add Bybit and OKX adapters.
7. Add KuCoin, Kraken, and Interactive Brokers adapters.
8. Remove legacy direct exchange dependencies.

---

# Final Recommendation

APEX should move from a Binance-specific integration to a formal Exchange Abstraction Layer before adding Bybit, OKX, KuCoin, Kraken, or Interactive Brokers. The highest-priority foundations are the exchange interface, adapter registry, unified order model, order idempotency, retry/error taxonomy, and reconciliation workflow. Without these, adding more exchanges will increase operational risk and make live trading unsafe.
