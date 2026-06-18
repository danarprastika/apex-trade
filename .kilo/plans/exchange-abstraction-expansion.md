# Exchange Abstraction Expansion Plan

## Goal
Expand APEX exchange abstraction from the current single-Binance read-only implementation into a full multi-exchange trading layer supporting Binance, Bybit, OKX, KuCoin, Kraken, and Interactive Brokers.

## Current State: Gap Analysis

The existing implementation defines an elegant adapter architecture with `ExchangeAdapter` / `MarketDataAdapter` / `OrderAdapter` / `PositionAdapter` protocols, base classes, rate limiting, retry, circuit breaker, failover, and error mapping. `ExchangeCapabilityCatalog` already declares six exchanges. However, only the Binance adapter is implemented, and it covers only three operations: `fetch_candles`, `fetch_ticker`, and `fetch_balances`. All trading capabilities (`submit_order`, `cancel_order`, `fetch_order`, `fetch_positions`, etc.) are set to `False` across the catalog.

This means the "exchange abstraction" is currently a **data-fetch abstraction**, not a **trading abstraction**.

## Missing Components

1. **Authentication per exchange** — API key/secret selection, testnet vs. production, session configuration.
2. **Order lifecycle adapters** — submit, cancel, modify, fetch for all six exchanges.
3. **Position and balance unification** — `fetch_positions` for futures exchanges, balance normalization across spot/margin.
4. **WebSocket / streaming** — Order book depth, user data stream for fills and order status updates.
5. **Asset metadata** — Precision rules (min/max qty, price step, tick size), contract details for futures, currency metadata.
6. **Fee schedule** — Per-exchange, per-tier commission and maker/taker fee lookup in unified model.
7. **Exchange health / rate-limit headers** — Exchange-aware response parsing for rate-limit windows and IP limits.
8. **Testnet / sandbox routing** — Per-adapter environment switching not just via ccxt options.
9. **Unified error categories** — Current mapper relies on keyword matching in error string; adapter-specific mapping needed.
10. **Instrument normalization** — Symbol normalization differs per exchange beyond the simple `replace("/", "")` used today.

## Adapter Architecture (Recommended)

Keep the existing four-protocol pattern. Add two new protocols to support streaming and lifecycle:

```
IExchangeAdapter (base capabilities + health)
├── IMarketDataAdapter    ← candles, ticker, order book, trades, funding, open interest
├── IOrderAdapter         ← submit, cancel, modify, fetch order status
├── IPositionAdapter      ← fetch positions, margin utilization
└── IStreamingAdapter     ← WebSocket streams (depth, ticker, user trades, order updates)
```

Base implementation remains `BaseExchangeAdapter`. Each exchange gets:

```
integrations/exchanges/
├── <exchange>/
│   ├── adapter.py
│   ├── websocket.py          ← optional; reuses ccxt WebSocket where available
│   ├── fees.py               ← fee schedule and precision metadata constant
│   └── mapping.py            ← error-mapper, symbol-normalizer overrides
```

Use ccxt Pro as the primary transport for unified fields. For exchanges not in ccxt (Interactive Brokers), implement the protocol directly against the exchange SDK/REST API.

## Interface Improvements

| Improvement | Rationale |
|-------------|-----------|
| Add pagination parameters to `fetch_candles`, `fetch_trades`, `fetch_orders` | ccxt supports `limit`/`params` pagination; many exchanges paginate deep history. |
| Add idempotency key in `ExchangeOperationContext` for `submit_order` | Prevent duplicate orders on retry. |
| Add `instrument_metadata` lookup on adapter (`get_instrument(symbol)`) | Centralize precision rule and minimums, used by order validation before submission. |
| Add `get_rate_limit_status()` on adapter | Expose exchange-provided rate-limit headers (Binance `X-MBX-USED-WEIGHT`). |
| Add async protocol versions (`async def`) for all methods | Current base is sync-style but event loop is used elsewhere; standardize on async for IO-bound exchange calls. |
| Add typed result wrapper (`UnifiedResult`) | Wrap all method returns with `ok: bool`, `data`, `error`, and `retry_after` for retry orchestration. |

## Data Model Standardization

Extend `app/domain/exchange/models.py` with:

- `InstrumentMetadata` — symbol, base, quote, status, min_qty, max_qty, step_size, tick_size, min_notional, leverage tiers, contract size.
- `FeeSchedule` — maker_fee, taker_fee, commission_currency, tier thresholds per exchange.
- `UnifiedTrade` — extends `UnifiedOrder` with fee breakdown, realized PnL, and counterparty info for futures.
- `ExchangeEnvironment` — enum of `production`, `testnet`, `sandbox`.

Normalize across exchanges:

| Field | Standard |
|-------|----------|
| Timestamps | UTC datetime |
| Quantity | Decimal in base asset |
| Price | Decimal in quote asset |
| Side | BUY / SELL (spot), LONG / SHORT (futures) |
| Status | NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED, EXPIRED |
| Order type | MARKET, LIMIT, STOP, STOP_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT |
| Time in force | GTC, IOC, FOK, GTD |
| Error category | Enum `ExchangeErrorCategory` from value_objects |

## Rate Limit Strategy

Current strategy: per-operation token bucket inside each adapter.

| Concern | Current | Revised |
|---------|---------|---------|
| Scope | Per adapter, per operation | Per adapter, per IP or per API key depending on exchange limits |
| Feedback | Token bucket blocks before call | Parse exchange response headers (`X-MBX-USED-WEIGHT-1M`, etc.) after call to correct drift |
| Backoff | None | Adaptive backoff when limits near threshold; sleep before 429 is returned |
| Global limits | None | Registry-level counter for cross-adapter rate budgets (relevant for shared IPs) |
| WebSocket frame rate | None | Dedicated rate limiter for WS subscriptions and pings |

## Retry Strategy

Current strategy: fixed exponential backoff with jitter in `RetryManager`, triggered per-exception.

| Concern | Current | Revised |
|---------|---------|---------|
| Context propagation | Loses `ExchangeOperationContext` on retry | Propagate `request_id`, `idempotency_key` through retry loop |
| Retry budget | Global `max_attempts=3` | Per-exchange config (e.g., Kraken less tolerant; IBKR may require 5+ attempts on market data) |
| Backoff calibration | Fixed base delay | Exchange-aware: use `Retry-After` header when present; otherwise exponential |
| Non-retryable errors | Relies on error mapper string matching | Add exchange-specific exception classes to surface canonical category from adapter |
| Outer orchestration | Adapter-internal only | Add `ExchangeOperationExecutor` that wraps adapter method with circuit breaker → rate limit check → retry → result wrapper |

## Failover Strategy

Current `ExchangeFailoverManager` evaluates a static pluggable policy and finds the first eligible adapter in the registry.

| Concern | Current | Revised |
|---------|---------|---------|
| Health awareness | Ignores circuit breaker state in routing | Route only to adapters whose `circuit_breaker.state == CLOSED` or `HALF_OPEN` |
| Market data failover | All-or-nothing per exchange | Per-symbol routing: route unavailable symbol to secondary exchange with same normalized symbol |
| Order execution failover | None | Requires failover-safe `idempotency_key`; fallback exchange must accept same key idempotently |
| State consistency | None | Failover should not re-submit already accepted orders; reconcile via `fetch_order` before retry |
| Weighted selection | None | Add priority/weight in catalog (e.g., primary vs. secondary exchange per region) |
| Data reconciliation | None | Post-failover snapshot comparison (` MarketDataReconciler`) to detect stale prices from failover source |

## Migration Plan

### Phase 1: Interface Stabilization (Weeks 1–2)

Objective: Harden the current four protocols and add the two new protocols (`IStreamingAdapter`, improved base).

- Add `UnifiedResult` wrapper to `IExchangeAdapter` methods.
- Add pagination params to market data methods.
- Add `InstrumentMetadata` and `get_instrument()` to `BaseExchangeAdapter`.
- Add async method signatures across protocols and `interfaces/protocols.py`.
- Write adapter conformance tests (each adapter must implement `IExchangeAdapter` + `IMarketDataAdapter`).

### Phase 2: Trading Path Completion (Weeks 3–5)

Objective: Implement `submit_order`, `cancel_order`, `fetch_order`, `fetch_positions` for Binance and add OKX.

- Binance Spot: full order lifecycle via ccxt.
- OKX Spot: full order lifecycle via ccxt (similar code path).
- Add `order_management.py` service to map `UnifiedOrder` status transitions to DB `Order` status.
- Add `exchange_account_id` → adapter resolution with credentials from `ExchangeAccount`.
- Add idempotency key generation and header injection in `ExchangeOperationContext`.

### Phase 3: Futures and Multi-Asset (Weeks 6–8)

Objective: Add Bybit and KuCoin adapters for spot + futures.

- Bybit adapter: spot + perpetual swap; funding rate and open interest.
- KuCoin adapter: spot + futures; handle KuCoin-specific symbol naming and margin tiers.
- Add `IPositionAdapter` methods.
- Add instrument metadata module for each exchange (min qty, tick size, leverage tiers).
- Add fee schedule data model.

### Phase 4: Traditional Markets (Weeks 9–11)

Objective: Add Kraken and Interactive Brokers adapters.

- Kraken: spot + futures; handle Kraken-specific pair naming and REST quirks.
- Interactive Brokers: implement against IBKR client API directly (not ccxt); map IBKR contract details to unified model; support stocks, ETFs, forex, futures.
- Add exchange-specific retry and rate-limit overrides (IBKR is polling-based; different cadence).

### Phase 5: Production Hardening (Weeks 12–13)

Objective: Reliability, observability, and operational maturity.

- Instrument all exchange calls with latency and error metrics (see observability roadmap).
- Add per-exchange WebSocket streams for order and balance updates.
- Implement market data failover per symbol.
- Add reconciliation job to compare exchange-reported balances/positions with internal DB state.
- Run chaos tests (adapter failure, rate limit, circuit breaker open).
- Update `ExchangeCapabilityCatalog` to reflect implemented adapters ( Binance and OKX should show `submit_order=True`, etc.).

## Scalability Considerations

### Request and connection scaling
- Use a registry-level `ExchangeOperationExecutor` so retries, rate limits, circuit breakers, metrics, and result wrapping are applied consistently without duplicating logic in every adapter.
- Keep per-exchange token buckets for exchange-specific limits, but add a shared budget layer for cases where multiple adapters run behind the same IP, proxy, or account group.
- Prefer async adapters for all IO-bound calls. Avoid blocking calls inside the event loop; use dedicated worker pools only for SDKs that do not expose async APIs, such as Interactive Brokers.
- Reuse HTTP sessions and WebSocket connections per exchange/account/environment instead of creating new clients for every request.
- Separate market data, account data, and order execution clients where an exchange enforces different limits for each path.

### State and metadata scaling
- Treat instrument metadata as cacheable read-mostly data. Refresh on startup, then periodically or when an unknown symbol is requested.
- Store precision, min/max quantity, contract size, and fee metadata in a normalized cache keyed by `(exchange, environment, symbol, market_type)` to avoid repeated `/symbols` or `/instruments` calls.
- Avoid hard-coding large symbol tables in adapters. Prefer exchange-provided metadata with small override files only for edge cases.
- Use UTC datetimes and `Decimal` values throughout the unified layer to avoid locale, floating-point, and daylight-saving issues.

### Order lifecycle scaling
- Generate idempotency keys at the service layer and propagate them through retries and failover.
- Before retrying an order submission after a timeout, reconcile with `fetch_order` using the idempotency key or client order ID when the exchange supports it.
- Do not fail over order execution by default. Fallback order routing should be explicit, exchange-supported, and reconciled to avoid duplicate fills.
- Keep order status normalization in one mapping layer so exchange-specific states do not leak into application services.

### Streaming scaling
- Use one WebSocket manager per exchange/account/environment and multiplex subscriptions for depth, ticker, trades, and user data.
- Add exponential backoff with jitter for reconnects, then resubscribe with the same normalized symbol set.
- Apply a separate frame-rate limiter for subscription changes and ping messages.
- Emit stream health metrics: connection age, reconnect count, dropped frames, subscription count, and last message timestamp.

### Observability and operations
- Log every external call with exchange, account, operation, symbol, duration, status, request ID, and retry attempt.
- Redact API keys, secrets, signatures, tokens, and full request bodies before logging.
- Track latency, error rate, retry rate, circuit breaker transitions, rate-limit hits, WebSocket disconnects, and stale-data duration per exchange.
- Add operational runbooks for API key rotation, testnet/production misrouting, exchange outage, duplicate-order reconciliation, and WebSocket outage.

### Security and compliance
- Load credentials from `ExchangeAccount` records or secure environment secrets; never store secrets in adapter code or plan files.
- Separate testnet, sandbox, and production credentials and require explicit environment selection.
- Validate order parameters against instrument metadata before sending orders.
- Keep Interactive Brokers routing decisions conservative: paper account by default for development, explicit production opt-in only.

## Remaining Report Sections

### Testing strategy
- Unit tests: symbol normalization, fee lookup, instrument metadata normalization, error mapping, and order status mapping for each exchange.
- Adapter conformance tests: each implemented adapter must expose the same method signatures and return `UnifiedResult`.
- Contract tests: mock exchange responses for success, retryable errors, non-retryable errors, rate limits, circuit breaker trips, and WebSocket reconnects.
- Integration tests: Binance testnet order placement, order fetch, cancellation, balance fetch, and market data fetch.
- Failover tests: market data routes to healthy secondary exchanges; order execution does not duplicate submissions after timeout.
- Chaos tests: simulated exchange outage, slow responses, malformed payloads, stale metadata, and WebSocket disconnect storms.

### Deployment and configuration
- Add exchange configuration records for credentials, environment, enabled markets, and priority weights.
- Keep exchange-specific tuning in small configuration objects rather than branching application services.
- Default new adapters to disabled in production until conformance and integration tests pass.
- Add migration checks for any new `ExchangeAccount` fields, such as environment, API scope, and account subtype.

### Rollout plan
- Roll out market data adapters before trading adapters.
- Enable testnet trading on Binance first, then OKX, then Bybit and KuCoin.
- Add Kraken after symbol normalization and fee metadata are stable.
- Add Interactive Brokers last because it uses a different SDK, polling model, and instrument universe.
- Use feature flags per exchange and per operation so market data, balances, positions, and order execution can be enabled independently.

## Implementation Roadmap

### Phase 1: Interface Stabilization and Unified Result Wrapper
- Add `UnifiedResult`, `InstrumentMetadata`, `FeeSchedule`, and `ExchangeEnvironment` to `app/domain/exchange/models.py`.
- Add async method signatures to `interfaces/protocols.py`.
- Add `get_instrument`, `get_fee_schedule`, and `get_rate_limit_status` to the base adapter contract.
- Add pagination parameters to market data methods.
- Add idempotency key support to `ExchangeOperationContext`.
- Convert Binance adapter methods to return `UnifiedResult`.

### Phase 2: Binance Trading Completion and OKX Adapter
- Implement Binance `submit_order`, `cancel_order`, `fetch_order`, and `fetch_positions` through ccxt with testnet routing.
- Implement OKX market data and order lifecycle adapters.
- Add order status mapping and `order_management.py` reconciliation service.
- Add idempotency key generation and client-order-ID propagation.
- Add adapter conformance tests for Binance and OKX.

### Phase 3: Bybit and KuCoin Spot/Futures
- Add Bybit spot and perpetual swap adapters.
- Add KuCoin spot and futures adapters.
- Add funding rate, open interest, and position normalization.
- Add exchange-specific symbol normalization for futures and margin markets.
- Add instrument metadata and fee schedule loaders.

### Phase 4: Kraken and Interactive Brokers
- Add Kraken adapter with Kraken-specific pair normalization and REST quirks.
- Add Interactive Brokers adapter using the IBKR client API directly.
- Map IBKR contracts, account summaries, orders, executions, and positions into the unified model.
- Add IBKR polling, retry, and rate-limit configuration separate from REST exchanges.

### Phase 5: Production Hardening
- Add metrics, structured logging, and dashboards for latency, error rate, retry rate, circuit breaker state, and WebSocket health.
- Add per-symbol market data failover.
- Add reconciliation jobs for balances, positions, and orders.
- Add chaos tests for adapter failure, rate-limit pressure, stale metadata, and WebSocket reconnect storms.
- Update `ExchangeCapabilityCatalog` so implemented operations are accurate.

## Final Acceptance Criteria

1. `ExchangeCapabilityCatalog` accurately reflects implemented adapters and supported operations.
2. Binance and OKX support `submit_order`, `cancel_order`, `fetch_order`, `fetch_balances`, and `fetch_positions` end-to-end in testnet or sandbox.
3. Bybit and KuCoin support spot market data and position fetch; futures support is marked explicitly in the catalog.
4. Kraken supports market data, balances, and order fetch; Interactive Brokers supports market data, balances, positions, and order fetch through the IBKR API.
5. All implemented adapters conform to `IExchangeAdapter`, `IMarketDataAdapter`, `IOrderAdapter`, and `IPositionAdapter` where applicable.
6. All adapter methods return `UnifiedResult` and include `retry_after` when rate-limit or transient failures occur.
7. `ExchangeFailoverManager` respects circuit breaker state and routes market data per symbol to healthy alternatives.
8. `RetryManager` propagates `ExchangeOperationContext`, `request_id`, and `idempotency_key` through retries.
9. `RateLimitManager` applies per-adapter budgets and adjusts limits using exchange-provided reset or usage headers when available.
10. Unified instrument metadata covers `min_qty`, `max_qty`, `step_size`, `tick_size`, `min_notional`, contract size, and market type for each supported symbol.
11. End-to-end order placement, fetch, and cancellation succeed on Binance testnet.
12. WebSocket streaming delivers real-time depth and order updates for at least one exchange.
13. Observability dashboards show latency, error rate, retry rate, circuit breaker transitions, and volume per exchange.
14. Duplicate order safeguards are verified by retry and timeout tests.
15. Credentials, API scopes, environments, and production opt-ins are validated before trading is enabled.
