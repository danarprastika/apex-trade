# Event-Driven Architecture for APEX

## Overview

This document outlines the Event-Driven Architecture (EDA) design for APEX, enabling asynchronous, decoupled communication between modules through a central event bus system.

---

## 1. Event Bus Architecture

### 1.1 Core Components

```
┌────────────────────────────────────────────────────────────────┐
│                     EVENT BUS (Redis Streams)                     │
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │  Producer        │  │  Consumer        │  │  Stream     │ │
│  │  Modules         │  │  Modules         │  │  Manager    │ │
│  └──────────────────┘  └──────────────────┘  └─────────────┘ │
│         │                        │                    │        │
│         └────────────────────────┴────────────────────┘        │
│                         Publish Events                           │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    MESSAGE BROKER LAYER                          │
│  Redis Streams + Redis Pub/Sub (for low-latency events)           │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Event Bus Types

| Bus Type | Use Case | Latency | Persistence |
|----------|----------|---------|-------------|
| **Command Bus** | Direct commands requiring response | <10ms | No |
| **Event Bus** | Domain events for async processing | <100ms | Yes (Redis Streams) |
| **Broadcast Bus** | Real-time market updates | <50ms | No (Redis Pub/Sub) |
| **Audit Bus** | Compliance and logging | <1s | Yes (Redis Streams + DB) |

### 1.3 Event Schema

```python
@dataclass
class ApexEvent:
    type: str              # e.g., "MARKET.UPDATED", "SIGNAL.GENERATED"
    payload: dict[str, Any]
    id: str              = uuid4()
    occurred_at: datetime = now_utc()
    correlation_id: str | None = None  # For tracing
    source: str | None = None  # Originating module
    priority: int = 0  # Higher = more important
```

### 1.4 Subscription Model

- **Fan-out**: One event → Multiple handlers
- **Competing Consumers**: Multiple instances → One handler per event
- **Priority Queue**: Critical events processed first
- **Dead Letter Queue**: Failed events after max retries

---

## 2. Event Types

### 2.1 Market Data Events

| Event Type | Payload | Trigger |
|------------|---------|---------|
| `MARKET.PRICE_UPDATED` | `symbol, price, timestamp, exchange` | Price ticker update |
| `MARKET.CANDLE_CLOSED` | `symbol, timeframe, candle, indicators` | New candle completes |
| `MARKET.ORDERBOOK_UPDATED` | `symbol, bids, asks, spread` | Orderbook change |
| `MARKET.FUNDING_UPDATED` | `symbol, funding_rate, timestamp` | Funding rate change |
| `MARKET.VOLUME_SPIKE` | `symbol, volume, avg_volume, spike_ratio` | Volume > 2x average |

### 2.2 Signal Engine Events

| Event Type | Payload | Trigger |
|------------|---------|---------|
| `SIGNAL.GENERATED` | `strategy_id, signal, confidence, market_data` | Strategy produces signal |
| `SIGNAL.VALIDATED` | `signal_id, validation_result` | Signal passes validation |
| `SIGNAL.REJECTED` | `signal_id, reason, veto_source` | Signal fails validation |

### 2.3 Risk Engine Events

| Event Type | Payload | Trigger |
|------------|---------|---------|
| `RISK.PROFILE_UPDATED` | `user_id, profile, changes` | Risk profile change |
| `RISK.LIMIT_BREACH` | `user_id, limit_type, current, threshold` | Risk limit exceeded |
| `RISK.VETO_APPLIED` | `signal_id, veto_reason, risk_score` | Trade vetoed |

### 2.4 Execution Engine Events

| Event Type | Payload | Trigger |
|------------|---------|---------|
| `ORDER.CREATED` | `order_id, signal_id, params` | Order created |
| `ORDER.SUBMITTED` | `order_id, exchange_id` | Sent to exchange |
| `ORDER.FILLED` | `order_id, fill_price, fill_qty` | Partial/full fill |
| `ORDER.CANCELLED` | `order_id, reason` | Order cancelled |
| `TRADE.OPENED` | `trade_id, entry, position` | New position opened |
| `TRADE.CLOSED` | `trade_id, exit, pnl` | Position closed |

### 2.5 Portfolio Engine Events

| Event Type | Payload | Trigger |
|------------|---------|---------|
| `PORTFOLIO.UPDATED` | `user_id, balances, positions` | Portfolio sync |
| `POSITION.OPENED` | `position_id, symbol, qty, entry` | Position created |
| `POSITION.MODIFIED` | `position_id, pnl, tp, sl` | PnL update |
| `POSITION.CLOSED` | `position_id, exit, realized_pnl` | Position closed |

### 2.6 AI Modules Events

| Event Type | Payload | Trigger |
|------------|---------|---------|
| `AI.MODEL_TRAINED` | `model_id, version, metrics` | Model training complete |
| `AI.PREDICTION_MADE` | `prediction_id, asset, value, confidence` | Prediction generated |
| `AI.DECISION_MADE` | `decision_id, recommendation, reasoning` | AI decision output |
| `AI.LEARNING_TRIGGERED` | `source_event, feature_importance` | Learning cycle started |

---

## 3. Event Flow

### 3.1 Complete Trade Flow

```
┌─────────────────┐
│ Market Collector │
└────────┬────────┘
         │ MARKET.CANDLE_CLOSED
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Strategy Engine │────▶│ Signal Engine   │────▶│ Risk Engine     │
│ (Subscribed)    │     │ (Generates)     │     │ (Validates)     │
└─────────────────┘     └────────┬──────────┘     └────────┬────────┘
         │                      │ SIGNAL.GENERATED       │ RISK.VETO_APPLIED
         │                      ▼                        │
         │               ┌─────────────────┐             │
         │               │ Event Bus       │◀────────────┘
         │               └────────┬────────┘
         │                      │ SIGNAL.VALIDATED
         │                      └────────┬────────────────┐
         │                               │ ORDER.CREATED    │
         │                               ▼                 │
         │               ┌─────────────────────────────┐    │
         │               │ Execution Engine            │    │
         │               │ (Consumes VALIDATED signals)  │    │
         │               └────────┬────────────────────┘    │
         │                      │ TRADE.OPENED            │
         │                      ▼                         │
         │               ┌─────────────────┐               │
         │               │ Portfolio Engine│               │
         │               │ (Updates pos)   │               │
         │               └─────────────────┘               │
         │                                                │
         └────────────────────────────────────────────────┘
```

### 3.2 AI Learning Flow

```
TRADE.CLOSED ──▶ AI.LEARNING_TRIGGERED ──▶ Model Updates
       │               │
       ▼               ▼
[Trade data]    [Feature store] ──▶ Training pipeline ──▶ AI.MODEL_TRAINED
```

### 3.3 Event Correlation

Use `correlation_id` to trace related events:
1. Market update → Signal generated
2. Signal validated → Order created
3. Order filled → Trade opened
4. Trade closed → Learning triggered

---

## 4. Failure Handling

### 4.1 Event Failure Scenarios

| Scenario | Handling |
|----------|----------|
| **Handler Crash** | Move to DLQ, alert operators |
| **Handler Timeout** | Kill after 30s, retry with backoff |
| **Invalid Payload** | Log error, skip event, notify |
| **Redis Down** | Queue in memory, persist to disk |

### 4.2 Dead Letter Queue

```
DLQ Structure:
- event_id: Original event identifier
- error: Error message
- handler: Failed handler name
- retry_count: Attempts made
- first_failed: Timestamp
- payload: Original event data
```

### 4.3 Circuit Breaker Pattern

Each handler implements circuit breaker:
- **Closed**: Normal operation
- **Open**: After 5 consecutive failures, stop processing for 60s
- **Half-Open**: After timeout, allow 1 test event

### 4.4 Event Ordering Guarantees

- **FIFO within stream**: Redis Streams guarantees order
- **Idempotency**: Handlers must check `event_id` for duplicates
- **Exactly-once**: Use Redis stream consumer groups + manual ack

---

## 5. Retry Strategy

### 5.1 Exponential Backoff

```
Attempt 1: 1s
Attempt 2: 2s
Attempt 3: 4s
Attempt 4: 8s
Attempt 5: 16s
Max: 60s
After: DLQ
```

### 5.2 Retry Semantics

| Event Type | Retry Policy |
|------------|--------------|
| Market events | 3 retries, fast backoff |
| Signal events | 5 retries, medium backoff |
| Order events | 10 retries, slow backoff |
| Risk events | No retry (fail fast) |
| AI events | 3 retries, medium backoff |

### 5.3 Idempotency Keys

All handlers must implement idempotency:
- Check `event_id` against processed set
- Skip processing if already handled
- Store last N event IDs in Redis set

---

## 6. Scalability Strategy

### 6.1 Horizontal Scaling

- **Consumer Groups**: Multiple instances of same handler
- **Partition by Symbol**: Route events by trading pair
- **Partition by User**: User-based event isolation

### 6.2 Scaling Patterns

| Component | Scale Mechanism |
|-----------|-----------------|
| Strategy Engine | Scale by symbol group |
| Signal Engine | Stateless - unlimited |
| Risk Engine | Scale by user ID |
| Execution Engine | Scale by exchange |
| Portfolio Engine | Scale by user ID |
| AI Modules | GPU-bound - dedicated nodes |

### 6.3 Load Shedding

- **Priority-based dropping**: DROP events with priority < threshold
- **Rate limiting**: Max 1000 events/sec per consumer
- **Batch processing**: Group similar events (e.g. market updates)

### 6.4 Monitoring

| Metric | Target |
|--------|--------|
| Event latency | <100ms avg |
| Processing time | <50ms per event |
| Failure rate | <0.1% |
| DLQ size | <10 events |
| Backlog | <1000 pending |

### 6.5 Deployment

```
┌─────────────────────────────────────────┐
│           Kubernetes Deployment            │
├─────────────────────────────────────────┤
│ Event Bus (Redis Cluster)               │
│  ├── 3-node cluster                     │
│  └── Persistent volumes                 │
│                                        │
│ Consumer Pods                           │
│  ├── strategy-engine-1 (symbols A-M)   │
│  ├── strategy-engine-2 (symbols N-Z)   │
│  ├── signal-engine (auto-scale)        │
│  ├── risk-engine (user-sharded)       │
│  ├── execution-engine (exchange-based) │
│  └── portfolio-engine (user-sharded)   │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
- Enhanced EventBus with Redis Streams
- Event persistence layer
- DLQ implementation

### Phase 2: Module Integration
- Refactor modules to use events
- Add correlation IDs
- Implement idempotency

### Phase 3: Scaling
- Consumer groups setup
- Partitioning strategy
- Load shedding

### Phase 4: Monitoring
- Metrics collection
- Alerting rules
- Dashboard