# Backtesting Engine - Complete Design

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKTESTING ENGINE SUBSYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐      │
│  │   Backtest API   │   │   Backtest       │   │   Report         │      │
│  │   Endpoints      │──▶│   Service        │──▶│   Generator      │      │
│  └──────────────────┘   └─────────┬──────────┘   └──────────────────┘      │
│                                   │                                        │
│                                   ▼                                        │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐      │
│  │   Historical     │   │   Strategy       │   │   Performance    │      │
│  │   Data Loader    │──▶│   Tester         │──▶│   Metrics        │      │
│  └──────────────────┘   └─────────┬──────────┘   └─────────┬────────┘      │
│                                   │                      │               │
│                                   ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐             │               │
│  │   Market Data    │   │   Order &        │             │               │
│  │   Cache          │   │   Position       │             │               │
│  └──────────────────┘   │   Simulator      │             │               │
│                          │   (Slippage,    │             │               │
│                          │   Commission)    │             │               │
│                          └─────────┬──────────┘            │               │
│                                     │                      │               │
│  ┌──────────────────┐   ┌──────────▼──────────┐            │               │
│  │   Risk Service   │   │   Trade Recorder    │            │               │
│  │   (Backtest Mode)│   │   (Position/PnL)    │            │               │
│  └──────────────────┘   └─────────────────────┘            │               │
│                              │                           │               │
│                              ▼                           │               │
│                      ┌──────────────────┐                │               │
│                      │   Database       │◀─────────────┘               │
│                      │   Storage        │                                │
│                      └──────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **Event-Driven** | Backtest events flow through Redis Streams (existing event bus) |
| **Deterministic** | Same input produces identical results; all random seeds controlled |
| **Isolated** | Backtest runs do not affect live trading state |
| **Reversible** | All backtest data can be purged without affecting production |
| **Auditable** | Every backtest run produces comprehensive audit trail |
| **Reproducible** | Full configuration stored with each run |

---

## 2. Components

### 2.1 Core Components

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **HistoricalDataLoader** | Fetches, validates, and streams historical candles | SQLAlchemy queries, Redis cache |
| **BacktestSimulator** | Core engine executing strategy against market data | StrategyPlugin interface |
| **OrderSimulator** | Simulates order execution (MARKET, LIMIT, STOP) | Price-time priority matching |
| **PositionSimulator** | Tracks position lifecycle, PnL calculation | Position state machine |
| **SlippageSimulator** | Models realistic price impact on execution | Volume/volatility-based models |
| **CommissionSimulator** | Calculates trading costs per exchange | Maker/taker fee structures |
| **RiskValidator** | Validates signals against risk rules in backtest context | RiskService with backtest flag |
| **MetricsEngine** | Computes performance statistics and KPIs | Portfolio analytics formulas |
| **ReportGenerator** | Produces reports in PDF, HTML, CSV formats | Jinja2 templates |

### 2.2 Component Specifications

#### Historical Data Replay
- **Input**: Symbol, timeframe, date range, optional filters
- **Output**: Stream of candles in chronological order
- **Features**:
  - Instant replay (full speed)
  - Accelerated replay (configurable speed multiplier)
  - Data quality validation
  - Missing data detection and gap reporting
  - Multi-symbol synchronization
  - Redis caching for frequently accessed data

#### Strategy Tester
- Integrates with StrategyPlugin interface
- Calls `analyze(market_data)` for each candle
- Maintains strategy state across backtest run
- Produces SignalResult objects

#### Risk Validator
- Max positions check
- Daily loss limit check
- Drawdown limit check
- Exposure control
- Pre-trade risk checks for each signal

#### Position Simulator
- Entry tracking (price, time, quantity, side)
- SL/TP exit detection
- Realized/unrealized PnL
- Margin and leverage for futures
- Position status transitions (OPEN → CLOSED)

#### Order Simulator
- MARKET orders: Immediate execution at next available price
- LIMIT orders: Price-time priority matching
- STOP orders: Converts to MARKET when triggered
- Partial fill support

#### Slippage Simulation
| Model | Description | Configuration |
|-------|-------------|---------------|
| FIXED | Fixed percentage slippage | `max_slippage_pct` |
| VOLUME_BASED | Scales with volume ratio to average | `max_slippage_pct`, `volume_threshold` |
| VOLATILITY_BASED | Scales with price volatility | `max_slippage_pct` |
| HISTORICAL | Uses historical average slippage | `max_slippage_pct` |

#### Commission Simulation
| Model | Description | Configuration |
|-------|-------------|---------------|
| FLAT | Fixed percentage fee | `taker_fee`, `maker_fee` |
| EXCHANGE_TIER | Volume-based fee discounts | `maker_fee`, `taker_fee`, `volume_tier` |
| MAKER_TAKER | Separate maker/taker rates | `maker_fee`, `taker_fee` |

---

## 3. Database Impact

### 3.1 Existing Tables Already Extended

| Table | Current Extension |
|-------|-------------------|
| `backtest_runs` | Contains status, progress, error_details, initial_capital |
| `backtest_configs` | Contains position_sizing_method, slippage_model, commission_model |
| `backtest_sessions` | Contains market_pair_id, timeframe, candle_count, status |
| `backtest_trades` | Contains entry/exit prices, PnL, duration, timestamps |
| `backtest_metrics` | Contains metric_name, metric_value, metric_metadata |

### 3.2 Required Indexes

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

-- Session queries
CREATE INDEX idx_backtest_sessions_run 
ON backtest_sessions (backtest_run_id);
```

### 3.3 Partitioning Strategy

- `backtest_runs`: Partition by `user_id` for multi-tenant queries
- `backtest_trades`: Partition by `backtest_run_id` for parallel processing
- `backtest_metrics`: Partition by `backtest_run_id` for aggregation

---

## 4. Event Flow

### 4.1 Backtest Lifecycle Events

| Event Type | Payload | Trigger Point |
|------------|---------|---------------|
| `BACKTEST.STARTED` | `run_id, strategy_id, config, user_id` | User initiates backtest |
| `BACKTEST.PROGRESS` | `run_id, percentage, current_symbol, candle_time` | During execution |
| `BACKTEST.SIGNAL_GENERATED` | `run_id, signal_id, symbol, signal_type, confidence` | Strategy generates signal |
| `BACKTEST.SIGNAL_REJECTED` | `run_id, signal_id, reason, veto_source` | Risk veto or invalid |
| `BACKTEST.TRADE_OPENED` | `run_id, trade_id, symbol, entry_price, quantity` | Position opened |
| `BACKTEST.TRADE_CLOSED` | `run_id, trade_id, exit_price, pnl, duration` | Position closed |
| `BACKTEST.COMPLETED` | `run_id, total_trades, net_profit, metrics` | Successful completion |
| `BACKTEST.FAILED` | `run_id, error, failed_at` | Error during execution |

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
       │                      BACKTEST.SIGNAL_GENERATED         ▼
       │                                                   [RiskValidator]
       │                                                         │
       │                      BACKTEST.SIGNAL_REJECTED            │
       │                      BACKTEST.TRADE_OPENED              ▼
       │                                                   [OrderSimulator]
       │                                                         │
       │                      BACKTEST.TRADE_CLOSED              ▼
       │                                                   [PositionSimulator]
       │                                                         │
       │                      BACKTEST.TRADE_CLOSED              ▼
       │                                                   [MetricsEngine]
       │                                                         │
       ▼                                                         ▼
[Database] ────────────▶ [Event Store] ────────────▶ [ReportGenerator]
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
POST   /api/v1/backtests                      # Create backtest
GET    /api/v1/backtests                      # List user backtests
GET    /api/v1/backtests/{id}                 # Get backtest details
DELETE /api/v1/backtests/{id}                 # Cancel running backtest
GET    /api/v1/backtests/{id}/status          # Get backtest status
GET    /api/v1/backtests/{id}/progress        # Get real-time progress
```

### 5.2 Configuration Endpoints

```
POST   /api/v1/backtest-configs               # Create config
GET    /api/v1/backtest-configs               # List configs
GET    /api/v1/backtest-configs/{id}          # Get config
PUT    /api/v1/backtest-configs/{id}          # Update config
DELETE /api/v1/backtest-configs/{id}          # Delete config
```

### 5.3 Results Endpoints

```
GET    /api/v1/backtests/{id}/trades          # Get all trades
GET    /api/v1/backtest-trades/{id}            # Get single trade details
GET    /api/v1/backtests/{id}/metrics         # Get performance metrics
GET    /api/v1/backtests/{id}/equity          # Get equity curve data
GET    /api/v1/backtests/{id}/report         # Download report (PDF/HTML)
```

### 5.4 Request/Response Models

**BacktestCreateRequest:**
```json
{
  "strategy_id": "uuid",
  "config_id": "uuid",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "timeframe": "1h",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T00:00:00Z",
  "initial_capital": 10000.00,
  "position_sizing_method": "PERCENTAGE",
  "position_size_value": 2.0,
  "slippage_model": {
    "model": "VOLUME_BASED",
    "max_slippage_pct": 0.002
  },
  "commission_model": {
    "model": "EXCHANGE_TIER",
    "maker_fee": 0.001,
    "taker_fee": 0.001
  }
}
```

**BacktestRunResponse:**
```json
{
  "id": "uuid",
  "status": "PENDING",
  "progress": 0,
  "total_trades": 0,
  "net_profit": null,
  "created_at": "timestamp",
  "config": {
    "slippage_model": {...},
    "commission_model": {...},
    "position_sizing_method": "PERCENTAGE"
  }
}
```

---

## 6. Performance Metrics

### 6.1 Core Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Total Return | `(final_capital - initial_capital) / initial_capital` | Overall percentage return |
| Annualized Return | `(1 + total_return)^(365/days) - 1` | Annualized performance |
| Sharpe Ratio | `(return - risk_free_rate) / std_dev` | Risk-adjusted return |
| Max Drawdown | `max((peak - trough) / peak)` | Maximum portfolio decline |
| Win Rate | `winning_trades / total_trades` | Percentage of profitable trades |
| Profit Factor | `gross_profit / gross_loss` | Reward-to-risk ratio |
| Average Trade | `sum(net_profit) / count(trades)` | Mean profit per trade |
| Largest Win | `max(net_profit)` | Best single trade |
| Largest Loss | `min(net_profit)` | Worst single trade |
| Trades Per Day | `total_trades / days_in_backtest` | Trading frequency |

### 6.2 Additional Metrics

| Metric | Description |
|--------|-------------|
| Equity Curve | Time series of portfolio value |
| Monthly Returns | Returns broken down by month |
| Trade Duration Distribution | Histogram of trade holding times |
| Volatility | Standard deviation of returns |
| Recovery Factor | Return / Max Drawdown |
| Ulcer Index | Downside risk measure |

---

## 7. Implementation Phases

### Phase 1: Core Infrastructure (Complete)
- [x] Backtest database models
- [x] BacktestService with CRUD operations
- [x] SlippageCalculator and CommissionCalculator
- [x] PositionSizingCalculator

### Phase 2: Simulator Engine (In Progress)
- [x] BacktestPosition class
- [x] Strategy integration (analyze method)
- [ ] OrderSimulator for LIMIT/MARKET orders
- [ ] Enhanced SL/TP exit logic
- [ ] Risk validator integration

### Phase 3: Metrics & Reporting
- [ ] Extended metrics calculation
- [ ] Performance metric aggregation
- [ ] Report generator (PDF/HTML/CSV)
- [ ] Equity curve generation

### Phase 4: API & UI
- [ ] REST API endpoints
- [ ] WebSocket progress updates
- [ ] Frontend dashboard integration

---

## 8. Integration Points

| Existing Component | Integration |
|--------------------|-------------|
| Strategy Plugin System | Uses StrategyPlugin `analyze()` method |
| Event Bus | Publishes backtest lifecycle events |
| Risk Service | Validates signals in backtest mode |
| Market Data | Reads from `candles` table |
| Database | Persists backtest results |