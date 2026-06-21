# Sprint Breakdown

## 1. Sprint Planning Philosophy

Sprints follow **Scrum principles** adapted for solo/small team development. Each sprint delivers a **production-ready, tested, documented increment**.

**Sprint Duration**: 1 week (5 working days)
**Sprint Goal**: Clearly defined, deliverable increment

## 2. Overall Sprint Roadmap

```
Sprint 0:  Architecture & Foundation (Weeks 0-1)
Sprint 1:  Core Infrastructure (Weeks 2-3)
Sprint 2:  Domain Models (Weeks 4-6)
Sprint 3:  API & Exchange Integration (Weeks 7-8)
Sprint 4:  Telegram Bot Interface (Weeks 9-10)
Sprint 5:  Order Execution & Trading (Weeks 11-12)
Sprint 6:  Portfolio & AI Integration (Weeks 13-14)
Sprint 7:  Market Data Pipeline (Weeks 15-16)
Sprint 8:  Strategy Framework (Weeks 17-18)
Sprint 9:  Production Readiness (Weeks 19-20)
```

## 3. Sprint 0: Architecture & Foundation

**Goal**: Establish technical foundation and development environment.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Finalize architecture documents | P0 | Architecture | 3d | 20 docs complete, reviewed |
| Initialize repository | P0 | DevOps | 0.5d | Repo structure ready |
| Setup Python project (pyproject.toml) | P0 | Backend | 1d | Poetry install works |
| Configure development Docker Compose | P0 | DevOps | 1d | All services start |
| Setup CI/CD pipeline (GitHub Actions) | P0 | DevOps | 2d | Tests pass on PR |
| Configure linting and formatting | P0 | Backend | 0.5d | ruff + mypy pass |
| Setup testing framework | P0 | Backend | 1d | pytest + fixtures ready |
| Generate project structure | P0 | Backend | 1d | Folder architecture implemented |

**Outcomes**:
- Repository operational with CI/CD
- All 20 architecture documents committed
- Development environment reproducible

## 4. Sprint 1: Core Infrastructure

**Goal**: Database, caching, and configuration infrastructure.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| PostgreSQL+Docker configuration | P0 | Backend | 1d | Service starts, connects |
| SQLAlchemy 2.x setup (async) | P0 | Backend | 1.5d | Session factory works |
| Alembic migration setup | P0 | Backend | 0.5d | Initial migration created |
| Redis+Docker configuration | P0 | Backend | 0.5d | Service starts, connects |
| Pydantic Settings classes | P0 | Backend | 1d | All env vars loaded |
| Structured logging (structlog) | P1 | Backend | 1d | JSON logs to stdout |
| Base exception hierarchy | P0 | Backend | 0.5d | Core exceptions defined |
| Global error handlers | P1 | Backend | 1d | FastAPI exception handlers |

**Outcomes**:
- Database migrations run cleanly
- Redis caching operational
- Structured logging in place
- Environment variable management working

## 5. Sprint 2: Core Domain Models

**Goal**: Implement the foundational domain entities and value objects.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Base entity class | P0 | Domain | 0.5d | Identity, timestamps, equality |
| Value objects (Price, Quantity, Symbol) | P0 | Domain | 1d | Immutable, validated |
| Trade entity | P0 | Domain | 1d | With invariants |
| Order entity (Aggregate Root) | P0 | Domain | 1.5d | State machine, validation |
| Position entity | P0 | Domain | 1d | Open/closed logic |
| Portfolio aggregate | P0 | Domain | 2d | Balance management |
| Domain event base classes | P1 | Domain | 0.5d | Event pattern |
| Unit tests for domain | P0 | QA | 2d | > 90% coverage |

**Outcomes**:
- Domain layer 100% pure (no infra deps)
- Core business rules enforced
- Domain tests > 90%

## 6. Sprint 3: API & Exchange Integration

**Goal**: REST API and CCXT exchange connectivity.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| FastAPI app setup | P0 | Presentation | 0.5d | App starts on port 8000 |
| Health check endpoints | P0 | Presentation | 0.5d | /health/live, /health/ready |
| CCXT exchange adapter | P0 | Infrastructure | 2d | Connect to Binance testnet |
| Order repository (SQLAlchemy) | P0 | Infrastructure | 2d | CRUD operations |
| Portfolio repository | P0 | Infrastructure | 1.5d | Balance queries |
| PlaceOrder mutation | P0 | Application | 2d | Full order placement flow |
| GetPortfolio query | P0 | Application | 1d | Portfolio summary |
| API endpoint (POST /orders) | P1 | Presentation | 1d | Returns OrderResponse |
| API endpoint (GET /portfolio) | P1 | Presentation | 0.5d | Returns PortfolioResponse |
| Integration tests | P0 | QA | 1.5d | API + DB + Exchange |
| /docs endpoint | P1 | Presentation | 0.5d | Auto-generated docs |

**Outcomes**:
- API operational with first endpoints
- Exchange connectivity established
- Orders persist to database

## 7. Sprint 4: Telegram Bot Interface

**Goal**: Telegram as primary user control interface.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| aiogram 3.x setup | P0 | Presentation | 0.5d | Bot starts |
| Webhook configuration | P0 | Presentation | 0.5d | Receives updates |
| Auth middleware | P0 | Presentation | 1d | Telegram ID verification |
| Keyboard/Markup builders | P1 | Presentation | 1d | Inline keyboards |
| /start command | P0 | Presentation | 0.5d | Welcome and auth status |
| /buy command handler | P0 | Presentation | 1d | Parses and places order |
| /sell command handler | P0 | Presentation | 0.5d | Parses and places order |
| /portfolio command | P0 | Presentation | 0.5d | Shows summary |
| /analyze command | P1 | Presentation | 1d | AI market analysis |
| Error handling + retry | P1 | Presentation | 0.5d | Graceful degradation |
| Tests (unit + integration) | P0 | QA | 1.5d | Mock Telegram API |

**Outcomes**:
- Telegram bot responds to commands
- Primary user authenticated
- Basic trading via Telegram

## 8. Sprint 5: Order Execution & Lifecycle

**Goal**: Complete order lifecycle management.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| OrderOrchestrator service | P0 | Application | 2d | Coordinates order flow |
| OrderValidationService | P0 | Domain | 1d | Business rule checks |
| Risk check before execution | P0 | Domain | 1.5d | Balance, limits |
| CCXT order mapping | P0 | Infrastructure | 1d | Domain ↔ Exchange |
| Order status synchronization | P0 | Infrastructure | 2d | Poll exchange status |
| Order cancellation flow | P0 | Application | 1d | /cancel command |
| Position closing | P0 | Application | 1d | Market sell all |
| Trade creation after fill | P0 | Application | 1.5d | Domain event driven |
| NotificationService | P1 | Infrastructure | 1d | Telegram + future channels |
| /positions command | P1 | Presentation | 0.5d | List open positions |
| Tests | P0 | QA | 2d | E2E order flow |

**Outcomes**:
- Full order lifecycle: draft → open → filled/cancelled
- Trade records generated
- Positions tracked and displayable
- Notifications sent

## 9. Sprint 6: Portfolio & AI Integration

**Goal**: Portfolio management and basic AI analysis.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Portfolio valuation service | P0 | Domain | 1.5d | Calculate total value |
| P&L calculation | P0 | Domain | 1d | Realized + unrealized |
| Allocation tracking | P1 | Domain | 1d | Asset distribution |
| Performance metrics | P1 | Domain | 1d | Win rate, max drawdown |
| Gemini AI adapter | P0 | Infrastructure | 1.5d | API client |
| AI router with fallback | P1 | Infrastructure | 1d | Gemini → OpenRouter |
| Analysis use case | P0 | Application | 1.5d | Market analysis flow |
| Prompt management system | P0 | Infrastructure | 1d | Versioned prompts |
| AI response validation | P0 | Domain | 0.5d | Strict schema |
| /analyze command | P0 | Presentation | 0.5d | Enhanced analysis |
| Tests | P0 | QA | 1.5d | AI + Portfolio |

**Outcomes**:
- Portfolio value and P&L calculated
- Gemini AI integrated
- /analyze produces structured output

## 10. Sprint 7: Market Data Pipeline

**Goal**: Continuous real-time and historical market data.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| WebSocket connection | P0 | Infrastructure | 1.5d | CCXT WebSocket |
| CandleAggregationService | P0 | Domain | 1.5d | Timeframe resampling |
| Candle repository | P0 | Infrastructure | 1d | Store candles |
| Market data cache | P1 | Infrastructure | 1d | Redis hot cache |
| WebSocket broadcast | P1 | Infrastructure | 1d | Fan-out to clients |
| /market_data endpoint | P1 | Presentation | 1d | REST + WebSocket |
| Time-series partitioning | P2 | Infrastructure | 1d | PostgreSQL partitioning |
| Data validation | P0 | Infrastructure | 0.5d | Schema validation |
| Tests | P0 | QA | 1d | Pipeline + WebSocket |

**Outcomes**:
- Live candle streaming
- Historical candles queryable
- WebSocket real-time updates

## 11. Sprint 8: Strategy Framework

**Goal**: Define, backtest, and execute trading strategies.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Strategy entity | P0 | Domain | 1d | Definition model |
| Strategy repository | P0 | Infrastructure | 1d | CRUD |
| Strategy configuration | P0 | Infrastructure | 1d | YAML/JSON config |
| Backtest engine | P0 | Application | 3d | Simulate historical trades |
| Performance metrics calculator | P0 | Domain | 1d | Sharpe, drawdown, win rate |
| Backtest REST endpoint | P1 | Presentation | 0.5d | Run backtest via API |
| Strategy execution service | P0 | Application | 2d | Execute in paper or live |
| Signal generation | P0 | Application | 2d | From strategy rules |
| /strategy command | P1 | Presentation | 1d | Activate/deactivate |
| Tests | P0 | QA | 2d | Backtest + strategy |

**Outcomes**:
- Strategies definable via config
- Backtesting engine operational
- Strategies executable (paper trading first)
- Performance metrics calculated