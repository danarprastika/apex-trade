# APEX Backtesting Engine - Architectural Design

## 1. Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKTESTING ENGINE ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────┐ │
│  │  Historical     │     │   Backtest      │     │   Results   │ │
│  │  Data Loader    │────▶│  Simulator      │────▶│   Storage   │ │
│  │  (Market Data)  │     │                 │     │             │ │
│  └─────────────────┘     └────────┬────────┘     └─────────────┘ │
│                                   │                            │
│                                   ▼                            │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────┐ │
│  │   Strategy      │     │   Risk &        │     │   Report    │ │
│  │   Plugin        │────▶│   Position      │────▶│   Service   │ │
│  │   Interface     │     │   Simulator     │     │             │ │
│  └─────────────────┘     └─────────────────┘     └─────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **Event-Driven** | Backtest events flow through Redis Streams (existing event bus) |
| **Deterministic** | Same input produces identical results; no random on-the-fly data fetching |
| **Isolated** | Backtest runs do not affect live trading state |
| **Reversible** | All backtest data can be purged without affecting production |
| **Auditable** | Every backtest run produces comprehensive audit trail |

### 1.3 Integration with Existing APEX Architecture

The Backtesting Engine integrates as a **new subsystem** within the existing modular monolith:

- **Market Data**: Uses existing `candles` table for historical data
- **Strategy Interface**: Leverages existing Strategy Plugin System
- **Risk Engine**: Reuses Risk Service with backtest mode flag
- **Event System**: Publishes `BACKTEST.STARTED`, `BACKTEST.COMPLETED`, `BACKTEST.FAILED` events
- **Database**: New tables in `research` schema (existing backtest_runs table)

---

## 2. Components

### 2.1 Core Components

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **Historical Data Replay** | Fetches and streams historical market data at specified speed | Celery workers + Redis Streams |
| **Strategy Tester** | Executes strategy plugins against historical data | StrategyPlugin ABC (existing) |
| **Risk Validator** | Validates signals against risk rules in backtest context | RiskService extension |
| **Position Simulator** | Simulates position lifecycle with PnL calculation | Position domain model extension |
| **Order Simulator** | Simulates order execution without live exchange interaction | Order domain model extension |
| **Slippage Simulator** | Models realistic price impact on order execution | Configurable slippage models |
| **Commission Simulator** | Calculates trading costs during backtest | Exchange-specific fee models |
| **Performance Metrics** | Computes backtest statistics and KPIs | Custom metrics engine |
| **Report Generator** | Produces backtest reports in multiple formats | Report templates + exports |

### 2.2 Component Interactions

```
┌─────────────────────┐
│   BacktestRequest   │
│   (start_date,      │
│    end_date,         │
│    strategy_id,      │
│    symbols,          │
│    initial_capital)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ HistoricalDataLoader │────▶│ MarketDataStream    │
│                     │     │ (time-warped)       │
└─────────────────────┘     └──────────┬────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Strategy Plugin │     │ Risk Validator  │     │ Position Sim    │
│ (analyze)       │     │ (validate)      │     │ (track PnL)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                               │
                               ▼
               ┌────────────────────────────────────┐
               │        Order Simulator             │
               │  ┌─────────────────────────────┐   │
               │  │ Slippage & Commission       │   │
               │  │ Calculation                 │   │
               │  └─────────────────────────────┘   │
               └────────────────┬─────────────────────┘
                                │
                                ▼
               ┌────────────────────────────────────┐
               │        Trade Recorder              │
               └────────────────┬───────────────────┘
                                │
                                ▼
               ┌────────────────────────────────────┐
               │        Metrics Engine              │
               └────────────────┬───────────────────┘
                                │
                                ▼
               ┌────────────────────────────────────┐
               │        Report Generator            │
               └────────────────────────────────────┘
```

### 2.3 Detailed Component Specifications

#### 2.3.1 Historical Data Replay
- **Input**: Symbol, timeframe, date range, optional filters
- **Output**: Stream of candle data in chronological order
- **Features**:
  - Speed control (instant, accelerated, real-time)
  - Data quality validation before replay
  - Missing data detection and gap filling
  - Multi-symbol synchronization

#### 2.3.2 Strategy Tester
- **Integration**: Uses StrategyPlugin interface from strategy-plugin-system.md
- **Execution**: Calls `analyze(BacktestMarketData)` for each candle
- **State**: Maintains strategy state across backtest run
- **Output**: SignalResult objects for each signal generation

#### 2.3.3 Risk Validator
- **Checks**: Max positions, daily loss, drawdown, exposure limits
- **Context**: Uses backtest-specific risk profile
- **Validation**: Pre-trade risk checks for each signal
- **Veto**: Can reject signals based on risk rules

#### 2.3.4 Position Simulator
- **Tracking**: Entry price, quantity, side, stop loss, take profit
- **PnL**: Realized and unrealized PnL calculation
- **Lifecycle**: OPEN → CLOSED transitions based on SL/TP hits
- **Margin**: Margin and leverage simulation for futures

#### 2.3.5 Order Simulator
- **Types**: MARKET, LIMIT, STOP orders
- **Execution**: Simulates immediate or price-based fill
- **Matching**: Price-time priority matching algorithm
- **Partial fills**: Support for partial fill simulation

#### 2.3.6 Slippage Simulator
- **Models**:
  - Fixed: Fixed percentage or absolute slippage
  - Volume-based: Slippage proportional to volume ratio
  - Volatility-based: Slippage scaled by market volatility
  - Historical: Average slippage from historical data
- **Configuration**: Per-strategy or per-symbol settings

#### 2.3.7 Commission Simulator
- **Models**:
  - Exchange fee model (based on exchange tier)
  - Tiered fee structure (volume-based discounts)
  - Maker/taker distinction
  - Flat fee option

---

## 3. Database Impact

### 3.1 Existing Tables to Extend

| Table | Extension |
|-------|-----------|
| `backtest_runs` | Add `config JSONB`, `status`, `progress`, `error_details` |
| `paper_trades` | Rename to `backtest_trades` (or use as-is) |
| `signals` | Add `backtest_run_id` FK for traceability |

### 3.2 New Tables Required

#### `backtest_configs`
```sql
id UUID PK
strategy_id UUID FK strategies
name VARCHAR(100)
description TEXT
initial_capital NUMERIC
position_size_method VARCHAR(20) -- FIXED, PERCENTAGE, RISK_BASED
max_positions INTEGER
slippage_model JSONB
commission_model JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
```

#### `backtest_sessions`
```sql
id UUID PK
backtest_run_id UUID FK backtest_runs
symbol VARCHAR(50)
timeframe VARCHAR(10)
start_time TIMESTAMP
end_time TIMESTAMP
candle_count INTEGER
status VARCHAR(20) -- RUNNING, COMPLETED, FAILED
created_at TIMESTAMP
```

#### `backtest_trades`
```sql
id UUID PK
backtest_run_id UUID FK backtest_runs
backtest_session_id UUID FK backtest_sessions
signal_id UUID FK signals
entry_price NUMERIC
exit_price NUMERIC
quantity NUMERIC
gross_profit NUMERIC
commission_cost NUMERIC
slippage_cost NUMERIC
net_profit NUMERIC
duration_minutes INTEGER
opened_at TIMESTAMP
closed_at TIMESTAMP
INDEX: backtest_run_id, closed_at
```

#### `backtest_metrics`
```sql
id UUID PK
backtest_run_id UUID FK backtest_runs
metric_name VARCHAR(50)
metric_value NUMERIC
metric_metadata JSONB
INDEX: backtest_run_id, metric_name
```

### 3.3 Indexes for Backtesting Performance

```sql
-- Composite index for fast historical data lookup
CREATE INDEX idx_candles_backtest_lookup 
ON candles (market_pair_id, timeframe, open_time);

-- Backtest trade queries
CREATE INDEX idx_backtest_trades_run_closed 
ON backtest_trades (backtest_run_id, closed_at DESC);

-- Signal traceability in backtest
CREATE INDEX idx_signals_backtest_run 
ON signals (backtest_run_id, signal_time);
```

---

## 4. Event Flow

### 4.1 Backtest Lifecycle Events

| Event Type | Payload | Trigger Point |
|------------|---------|---------------|
| `BACKTEST.STARTED` | `run_id, strategy_id, config, user_id` | User initiates backtest |
| `BACKTEST.PROGRESS` | `run_id, percentage, current_symbol, candle_time` | During execution |
| `BACKTEST.TRADE_OPENED` | `run_id, trade_id, symbol, entry_price, quantity` | Position opened |
| `BACKTEST.TRADE_CLOSED` | `run_id, trade_id, exit_price, pnl, duration` | Position closed |
| `BACKTEST.COMPLETED` | `run_id, total_trades, net_profit, metrics` | Successful completion |
| `BACKTEST.FAILED` | `run_id, error, failed_at` | Error during execution |
| `BACKTEST.SIGNAL_GENERATED` | `run_id, signal_id, signal_data` | Strategy generates signal |
| `BACKTEST.SIGNAL_REJECTED` | `run_id, signal_id, reason` | Risk veto or invalid |

### 4.2 Event Flow Diagram

```
User API Request
       │
       ▼
[Backtest API]
       │
       ├── BACKTEST.STARTED ─────────────────────────────────────┐
       │                                                         │
       ▼                                                         ▼
[BacktestService] ──▶ [HistoricalDataLoader] ──▶ [MarketDataStream]
       │                                                         │
       │                                                         ▼
       │                                                [StrategyTester]
       │                                                         │
       │                      BACKTEST.SIGNAL_GENERATED            ▼
       │                                                   [RiskValidator]
       │                                                         │
       │                      BACKTEST.SIGNAL_REJECTED           │
       │                      BACKTEST.TRADE_OPENED              ▼
       │                                               [PositionSimulator]
       │                                                         │
       │                      BACKTEST.TRADE_CLOSED              ▼
       │                                                 [MetricsEngine]
       │                                                         │
       │                      BACKTEST.COMPLETED ──▶ [ReportGenerator]
       │                                                         │
       ▼                                                         ▼
[Database] ────────────▶ [Event Store] ────────────▶ [Notification]
```

### 4.3 Correlation and Tracing

All backtest events include:
- `correlation_id`: Links all events to the backtest run
- `backtest_run_id`: Direct reference to database record
- `sequence_number`: Order of events for replay
- `user_id`: Owner of the backtest

---

## 5. API Requirements

### 5.1 Backtest Management Endpoints

```
POST   /api/v1/backtests              # Create backtest
GET    /api/v1/backtests              # List user backtests
GET    /api/v1/backtests/{id}         # Get backtest details
DELETE /api/v1/backtests/{id}         # Cancel running backtest
GET    /api/v1/backtests/{id}/status  # Get backtest status
GET    /api/v1/backtests/{id}/progress # Get real-time progress
```

### 5.2 Configuration Endpoints

```
POST   /api/v1/backtest-configs        # Create config
GET    /api/v1/backtest-configs        # List configs
GET    /api/v1/backtest-configs/{id}    # Get config
PUT    /api/v1/backtest-configs/{id}    # Update config
DELETE /api/v1/backtest-configs/{id}    # Delete config
```

### 5.3 Results Endpoints

```
GET    /api/v1/backtests/{id}/trades    # Get all trades
GET    /api/v1/backtests/{id}/metrics   # Get performance metrics
GET    /api/v1/backtests/{id}/equity    # Get equity curve data
GET    /api/v1/backtests/{id}/report    # Download report (PDF/HTML)
```

### 5.4 Request/Response Models

**BacktestRequest:**
```json
{
  "strategy_id": "uuid",
  "config_id": "uuid",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "timeframe": "1h",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T00:00:00Z",
  "initial_capital": 10000.00,
  "position_sizing": {
    "method": "PERCENTAGE",
    "value": 2.0
  },
  "slippage": {
    "model": "VOLUME_BASED",
    "max_slippage": 0.002
  },
  "commission": {
    "model": "EXCHANGE_TIER",
    "maker_fee": 0.001,
    "taker_fee": 0.001
  }
}
```

**BacktestResponse:**
```json
{
  "id": "uuid",
  "status": "PENDING",
  "progress": 0,
  "total_trades": 0,
  "net_profit": null,
  "created_at": "timestamp"
}
```

---

## 6. Scalability Considerations

### 6.1 Horizontal Scaling

| Component | Scale Mechanism |
|-----------|-----------------|
| **Backtest Workers** | Scale by backtest run (each run is independent) |
| **Historical Data Loader** | Partition by symbol/timeframe |
| **Metrics Engine** | Stateless; unlimited parallelization |
| **Report Generator** | Asynchronous; queue-based processing |

### 6.2 Performance Optimizations

- **Caching**: Cache candles in Redis for frequently backtested periods
- **Parallel Symbol Processing**: Multi-symbol backtests can run in parallel
- **Incremental Progress**: Store checkpoint state for resume capability
- **Batch Metrics**: Compute metrics in batches rather than per-trade

### 6.3 Resource Management

| Resource | Limit |
|----------|-------|
| **Max concurrent backtests per user** | 3 |
| **Max concurrent backtests system-wide** | 20 |
| **Backtest data retention** | Configurable (default: 90 days) |
| **Report storage** | Separate from main database (S3/object storage) |

### 6.4 Scaling Architecture

```
┌─────────────────┐
│   API Layer     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Backtest Router │
│ (Fan-out to     │
│  worker pools)  │
└────────┬────────┘
         │
    ┌────┴────┬────┬────┐
    ▼         ▼    ▼    ▼
High     Medium  Low   Priority
Priority Pool  Pool  Pool  Queue
```

---

## 7. Gap Analysis

### 7.1 Against Existing Architecture

| Requirement | Current State | Gap | Resolution Approach |
|-------------|---------------|-----|---------------------|
| Historical Data Replay | `candles` table exists, market collector populates it | Need time-warped data streaming capability | Extend Market Data Service with backtest mode |
| Strategy Testing | Strategy Plugin System designed (see strategy-plugin-system.md) | No backtest execution framework | Create Backtest Simulator service |
| Risk Validation | Risk Service exists, risk profiles defined | No backtest-specific risk context | Extend Risk Service with backtest mode |
| Position Simulation | Position model exists, used for live trading | No simulation mode, needs PnL tracking | Extend Position model with simulation fields |
| Order Simulation | Order model exists | No simulation mode, needs slippage/commission | Extend Order model with simulation fields |
| Slippage/Commission | Not modeled | Missing entirely | Add to backtest_config model |
| Performance Metrics | Not implemented | Missing entirely | Create Metrics Engine component |
| Report Generation | Basic API response structure | No reporting infrastructure | Add Report Generator service |

### 7.2 Technical Gaps to Address

#### Missing Tables
- `backtest_configs` - Configuration templates
- `backtest_sessions` - Per-symbol session tracking
- `backtest_trades` - Trade-level results
- `backtest_metrics` - Performance metrics storage

#### Missing Service Layer
- `BacktestService` - Orchestrates backtest execution
- `BacktestSimulator` - Core simulation engine
- `BacktestMetricsService` - Performance calculation
- `BacktestReportService` - Report generation

#### Missing API Endpoints
- All backtest management endpoints (Section 5)

### 7.3 Integration Points

| Existing Component | Integration Point | Action Required |
|--------------------|-------------------|-----------------|
| Strategy Plugin System | StrategyPlugin interface | Add backtest context to analyze() |
| Event Bus | Redis Streams | Add backtest event types |
| Risk Service | Risk validation | Add backtest mode flag |
| Portfolio Service | Portfolio snapshots | Extend for backtest equity curves |

---

## 8. Implementation Priority

### Phase 1: Core Infrastructure
1. Create backtest database tables
2. Implement BacktestService with basic orchestration
3. Add backtest event types to event bus
4. Basic HistoricalDataLoader

### Phase 2: Simulation Engine
1. Extend Position/Order models for simulation
2. Implement PositionSimulator
3. Implement OrderSimulator with basic fills
4. Add Slippage and Commission models

### Phase 3: Risk & Metrics
1. Extend Risk Service for backtest mode
2. Implement Metrics Engine
3. Add performance metric calculations

### Phase 4: Reporting
1. Implement Report Generator
2. Add report templates
3. Export capabilities (PDF, HTML, CSV)

### Phase 5: API & UI Integration
1. Create API endpoints
2. Add WebSocket for real-time progress
3. Integrate with frontend dashboard