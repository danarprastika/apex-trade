# Overall System Architecture

## 1. System Topology

QuantX AI operates as a **personal, single-tenant trading platform** deployed on a single Linux VPS. The architecture follows a hexagonal/clean architecture pattern with distinct bounded contexts.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          External Interfaces                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ Telegram Bot │  │  Web UI      │  │  REST API   │  │  WebSocket│ │
│  │  (aiogram)   │  │  (React)     │  │  (FastAPI)  │  │  (Market) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ HTTPS / WSS
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway (Nginx)                           │
│                   Reverse Proxy + SSL Termination                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ Internal
┌─────────────────────────────────────────────────────────────────────┐
│                    Application Server (FastAPI)                      │
│                 ┌─────────────────────────────────┐                 │
│                 │  Presentation Layer             │                 │
│                 │  - Controllers                  │                 │
│                 │  - WebSocket Handlers           │                 │
│                 │  - Telegram Handlers            │                 │
│                 │  - DTOs / Schemas               │                 │
│                 └─────────────┬───────────────────┘                 │
│                               ↕                                     │
│                 ┌─────────────────────────────────┐                 │
│                 │  Application Layer              │                 │
│                 │  - Use Cases / Commands         │                 │
│                 │  - Service Orchestrators        │                 │
│                 │  - Event Handlers               │                 │
│                 │  - Repository Interfaces        │                 │
│                 └─────────────┬───────────────────┘                 │
│                               ↕                                     │
│                 ┌─────────────────────────────────┐                 │
│                 │  Domain Layer (Core)            │                 │
│                 │  - Entities                     │                 │
│                 │  - Value Objects                │                 │
│                 │  - Domain Services              │                 │
│                 │  - Aggregates                   │                 │
│                 │  - Domain Events                │                 │
│                 └─────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    Data & Infrastructure Layer                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐    │
│  │   PostgreSQL      │  │   Redis          │  │  External APIs   │    │
│  │   (Primary DB)    │  │   (Cache/Queue)  │  │  - CCXT Exchanges│    │
│  │   - Market Data   │  │   - Sessions     │  │  - Gemini API    │    │
│  │   - Portfolio     │  │   - Real-time    │  │  - OpenRouter    │    │
│  │   - Trades        │  │   - Rate Limit   │  │  - Telegram API  │    │
│  │   - Strategies    │  │   - Pub/Sub      │  │                  │    │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Bounded Contexts

### 2.1 Trading Context
Responsible for all trading operations, order management, and execution.
- **Core Operations**: Order placement, modification, cancellation
- **Domain Entities**: Order, Position, Trade, Portfolio
- **External Dependencies**: CCXT adapters for exchange connectivity

### 2.2 Market Data Context
Handles market data ingestion, caching, and normalization.
- **Core Operations**: Data fetching, aggregation, normalization
- **Domain Entities**: Candle, Tick, OrderBook, TradeRecord
- **External Dependencies**: CCXT WebSocket, REST endpoints

### 2.3 Analysis Context
AI-powered market analysis and signal generation.
- **Core Operations**: Pattern recognition, sentiment analysis, signal generation
- **Domain Entities**: Signal, Analysis, Indicator, Strategy
- **External Dependencies**: Gemini API, OpenRouter

### 2.4 Portfolio Context
Portfolio tracking, P&L calculation, and risk assessment.
- **Core Operations**: Balance tracking, P&L calculation, risk metrics
- **Domain Entities**: Balance, Position, Allocation, RiskMetrics
- **External Dependencies**: Trading context, Market data context

### 2.5 Notification Context
User communication across multiple channels.
- **Core Operations**: Message dispatch, alerting, reporting
- **Domain Entities**: Notification, Alert, Report
- **External Dependencies**: Telegram Bot API, Email (future)

### 2.6 Strategy Context
Backtesting, strategy validation, and optimization.
- **Core Operations**: Backtesting, parameter optimization, validation
- **Domain Entities**: Strategy, BacktestResult, OptimizationResult
- **External Dependencies**: Market data context, AI analysis

## 3. Deployment Topology

### Production (VPS)
```
┌────────────────────────────────────────────┐
│  Linux VPS (Ubuntu 22.04 LTS)              │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │  Docker Network: quantx_net          │  │
│  │                                      │  │
│  │  ┌────────────┐  ┌──────────────┐   │  │
│  │  │   Nginx    │  │   FastAPI    │   │  │
│  │  │  (Port:    │  │   (Port:     │   │  │
│  │  │   80/443)  │  │   8000)      │   │  │
│  │  └─────┬──────┘  └──────┬───────┘   │  │
│  │        │                │            │  │
│  │  ┌─────┴───────────┐    │            │  │
│  │  │                 │    │            │  │
│  │  │  PostgreSQL     │    │            │  │
│  │  │  (Port: 5432)   │◄───┘            │  │
│  │  └─────────────────┘                 │  │
│  │                                      │  │
│  │  ┌─────────────────┐                 │  │
│  │  │  Redis          │                 │  │
│  │  │  (Port: 6379)   │                 │  │
│  │  └─────────────────┘                 │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  Volumes:                                  │
│  - postgres_data (PostgreSQL persistence)   │
│  - redis_data (Redis persistence)           │
│  - uploads (report exports)                 │
│  - logs (application logs)                  │
└────────────────────────────────────────────┘
```

### Docker Network Isolation
- **quantx_net** (Docker bridge network)
  - Only containers within this network communicate
  - No direct external access to PostgreSQL or Redis
  - Nginx exposes only ports 80/443 to the internet
  - FastAPI accessible only via Nginx reverse proxy

## 4. Communication Patterns

### 4.1 Synchronous (HTTP/REST)
- User-initiated operations (trade placement, configuration updates)
- Web UI ↔ API layer
- Health checks and monitoring

### 4.2 Asynchronous (WebSocket)
- Real-time market data streaming
- Live portfolio updates
- Real-time risk alerts
- Chat-based notifications to Web UI

### 4.3 Event-Driven (Internal)
- Domain events trigger side effects
- Market tick events → Cache update → WebSocket broadcast
- Trade execution events → Portfolio recalculation → Notification

### 4.4 External Webhooks
- Telegram Bot API callbacks (aiogram webhook)
  - Alternative: Long polling for simplicity

## 5. Data Architecture

### 5.1 PostgreSQL (Primary Data Store)
```
Primary Responsibilities:
- Persistent trade history and positions
- Strategy configurations and parameters
- Historical market data (OHLCV)
- User preferences and settings
- Audit logs and compliance records

Schema Organization:
├── trading/         (orders, positions, trades)
├── market_data/     (candles, orderbooks, ticks)
├── strategy/        (strategies, backtests, signals)
├── portfolio/       (balances, allocations, performance)
├── system/          (configurations, logs, sessions)
└── ai_analysis/     (signals, predictions, reasoning)
```

### 5.2 Redis (Performance Layer)
```
Primary Responsibilities:
- Session management (Telegram + Web UI)
- Real-time market data cache
- Pub/Sub for WebSocket broadcasting
- Rate limiting for external APIs
- Temporary state (pending orders, calculations)
```

### 5.3 Time-Series Considerations
- PostgreSQL native for historical OHLCV
- Partitioning by time period for performance
- Aggregation strategies: 1m, 5m, 15m, 1h, 4h, 1d candles
- Archiving strategy for data > 2 years

## 6. AI Integration Architecture

### 6.1 Model Selection Strategy
```
┌─────────────────────────────────────────┐
│         AI Request Router               │
│                                         │
│  ┌─────────────┐    ┌───────────────┐  │
│  │  Primary    │───►│  Gemini API   │  │
│  │  (Gemini)   │    └───────────────┘  │
│  └─────────────┘                       │
│         ↕ (failover)                    │
│  ┌─────────────┐    ┌───────────────┐  │
│  │  Fallback   │───►│  OpenRouter   │  │
│  │  (OpenRouter)│   └───────────────┘  │
│  └─────────────┘                       │
└─────────────────────────────────────────┘
```

### 6.2 AI Service Responsibilities
- Market sentiment analysis
- Pattern recognition in price movements
- Natural language trade diary and journaling
- Strategy explanation generation
- Risk assessment assistance
- News/social media sentiment aggregation

### 6.3 Prompt Engineering Standards
- Domain-specific system prompts stored in configuration
- Context window management for market data
- Structured responses with JSON schemas
- Response validation and fallback strategies
- Logging of all AI interactions for auditability

## 7. Security Architecture

### 7.1 Defense in Depth
```
┌────────────────────────────────────────┐
│  Layer 7: User Authentication          │
│  - Telegram verified identity          │
│  - Web JWT/OAuth                       │
├────────────────────────────────────────┤
│  Layer 6: Application Authorization    │
│  - Role-based access (future-proof)    │
│  - API key management                   │
├────────────────────────────────────────┤
│  Layer 5: Input Validation             │
│  - Pydantic schemas                    │
│  - SQL injection prevention             │
├────────────────────────────────────────┤
│  Layer 4: Transport Security           │
│  - TLS 1.3 (Let's Encrypt)             │
│  - Secure WebSocket (WSS)              │
├────────────────────────────────────────┤
│  Layer 3: Network Security             │
│  - Docker network isolation            │
│  - Firewall rules (UFW)                │
│  - Rate limiting (Nginx)               │
├────────────────────────────────────────┤
│  Layer 2: Data Security                │
│  - Encrypted sensitive fields          │
│  - Audit logging                        │
│  - Backup encryption                    │
├────────────────────────────────────────┤
│  Layer 1: Infrastructure Security      │
│  - SSH key authentication only          │
│  - Automatic security updates           │
│  - Intrusion detection                  │
└────────────────────────────────────────┘
```

## 8. External Integrations

### 8.1 Exchange Connectivity (CCXT)
- Unified API abstraction for multiple exchanges
- Rate limiting per exchange
- Error handling and retry logic
- WebSocket streaming for real-time data
- REST API for order management

### 8.2 AI Providers
- **Primary**: Google Gemini API (JSON mode)
- **Fallback**: OpenRouter (multi-model support)
- Circuit breaker pattern for provider failures

### 8.3 Notification Channels
- **Primary**: Telegram (aiogram)
- **Future**: Email (SMTP)

## 9. Observability Architecture

### 9.1 Logging Strategy
- Structured JSON logging throughout
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Separate log streams per component

### 9.2 Metrics
- Application metrics (requests, latency, errors)
- Business metrics (trades executed, P&L, drawdown)
- System metrics (CPU, memory, disk)

### 9.3 Alerting
- Error rate thresholds
- P&L limit breaches
- System resource exhaustion
- Exchange connectivity failures

### 9.4 Health Checks
```
/health          - Overall system health
/health/live     - Liveness probe (Kubernetes-ready)
/health/ready    - Readiness probe (DB + Redis check)
/health/detailed - Component-specific status
```

## 10. Scalability Model

### Vertical Scaling (Primary)
- Single VPS with upgrade path
- Resource limits: 4vCPU / 16GB RAM / 500GB SSD
- Docker resource constraints per service

### Horizontal Considerations (Future)
- Stateful components (PostgreSQL) remain single-node
- Stateless components (FastAPI) can be scaled
- Redis Cluster for session distribution
- Load balancer for multiple API instances

## 11. Disaster Recovery

### RPO (Recovery Point Objective): 15 minutes
### RTO (Recovery Time Objective): 1 hour

### Backup Strategy
- **Database**: Daily automated backups with 30-day retention
- **Configuration**: Version controlled in git
- **Secrets**: Encrypted backup of secrets store
- **Logs**: 90-day retention for audit/compliance

### Recovery Procedures
1. Restore PostgreSQL from backup
2. Restore Redis state (if persistent)
3. Redeploy containers from image registry
4. Verify exchange API connectivity
5. Resume trading with dry-run verification
