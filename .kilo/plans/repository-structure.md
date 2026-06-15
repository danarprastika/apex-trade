# APEX Repository Structure Plan

## 1. Complete Repository Structure

```
apex-trade/
├── .github/                    # GitHub workflows, issue templates, dependabot
├── .kilo/                      # Kilo agent configuration
│
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/                # Presentation Layer
│   │   │   └── v1/
│   │   │       ├── admin/      # Admin endpoints (RBAC required)
│   │   │       ├── auth/       # Authentication endpoints
│   │   │       ├── health/     # Health check endpoints
│   │   │       ├── market/     # Market data endpoints
│   │   │       ├── notifications/ # Notification endpoints
│   │   │       ├── portfolio/  # Portfolio endpoints
│   │   │       ├── risk/       # Risk management endpoints
│   │   │       ├── trading/    # Trading endpoints
│   │   │       └── users/      # User management endpoints
│   │   │
│   │   ├── core/               # Core Module (Shared Kernel)
│   │   │   ├── config.py       # Configuration (env, pydantic settings)
│   │   │   ├── constants.py    # Application constants
│   │   │   ├── exceptions.py   # Custom exceptions
│   │   │   ├── logging.py      # Structured logging setup
│   │   │   ├── security.py     # Auth utilities, token handling
│   │   │   └── encryption.py   # Field encryption for sensitive data
│   │   │
│   │   ├── database/           # Infrastructure Layer
│   │   │   ├── base.py         # SQLAlchemy declarative base
│   │   │   ├── session.py      # DB session management
│   │   │   ├── models/         # Domain entities (SQLAlchemy models)
│   │   │   └── repositories/   # Repository pattern implementations
│   │   │
│   │   ├── domain/               # Domain Layer (Business Logic)
│   │   │   ├── entities/       # Domain entities (separate from SQLAlchemy models)
│   │   │   ├── value_objects/  # Value objects (Money, OrderId, etc.)
│   │   │   ├── events/         # Domain events
│   │   │   └── services/       # Domain services (business logic)
│   │   │
│   │   ├── services/           # Application Layer
│   │   │   ├── auth_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── exchange_service.py
│   │   │   ├── health_service.py
│   │   │   ├── market_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── paper_trading_service.py
│   │   │   ├── portfolio_service.py
│   │   │   ├── risk_service.py
│   │   │   ├── signal_service.py
│   │   │   ├── strategy_service.py
│   │   │   └── user_service.py
│   │   │
│   │   ├── tasks/              # Celery Background Tasks
│   │   │   ├── celery_app.py   # Celery instance configuration
│   │   │   ├── collectors/     # Data collection tasks
│   │   │   ├── schedulers/     # Scheduled task runners
│   │   │   └── workers/        # Background workers
│   │   │
│   │   ├── integrations/       # External service adapters
│   │   │   ├── binance/        # Binance exchange adapter
│   │   │   ├── redis/          # Redis client wrapper
│   │   │   └── telegram/       # Telegram bot integration
│   │   │
│   │   ├── middlewares/        # FastAPI middlewares
│   │   │   ├── audit.py        # Audit logging middleware
│   │   │   └── request_body.py # Request body middleware
│   │   │
│   │   ├── schemas/            # Pydantic schemas (DTOs)
│   │   │   ├── auth.py
│   │   │   ├── common.py
│   │   │   ├── exchange.py
│   │   │   ├── market.py
│   │   │   ├── notification.py
│   │   │   ├── portfolio.py
│   │   │   ├── risk.py
│   │   │   └── trading.py
│   │   │
│   │   ├── events/             # Event bus implementation
│   │   │   ├── bus.py
│   │   │   └── types.py
│   │   │
│   │   └── main.py             # Application entry point
│   │
│   ├── alembic/                # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── common/         # Generic components (Button, Card, etc.)
│   │   │   ├── layout/         # Layout components (Header, Sidebar, etc.)
│   │   │   ├── forms/          # Form components
│   │   │   └── guards/         # Route guards (AuthGuard, RoleGuard)
│   │   │
│   │   ├── features/           # Feature-based modules
│   │   │   ├── auth/           # Authentication feature
│   │   │   ├── trading/        # Trading feature
│   │   │   ├── portfolio/      # Portfolio feature
│   │   │   ├── market/         # Market data feature
│   │   │   ├── risk/           # Risk management feature
│   │   │   └── admin/          # Admin feature
│   │   │
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── api/            # API data hooks
│   │   │   └── ui/             # UI hooks (modals, forms, etc.)
│   │   │
│   │   ├── lib/                # Utilities and libraries
│   │   │   ├── api-client.ts   # Axios instance with interceptors
│   │   │   ├── auth.ts         # Auth utilities
│   │   │   └── utils.ts        # General utilities
│   │   │
│   │   ├── pages/              # Route components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── MarketPage.tsx
│   │   │   ├── TradingPage.tsx
│   │   │   ├── PortfolioPage.tsx
│   │   │   ├── NewsPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── AdminPage.tsx
│   │   │
│   │   ├── store/              # Zustand stores
│   │   │   ├── authStore.ts
│   │   │   └── uiStore.ts
│   │   │
│   │   ├── types/              # TypeScript types
│   │   │   └── api.ts
│   │   │
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── main.tsx
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── telegram-bot/              # aiogram Telegram Bot
│   ├── bot/
│   │   ├── handlers/           # Message/command handlers
│   │   ├── keyboards/          # Inline keyboards
│   │   ├── middlewares/        # Bot middlewares
│   │   ├── utils/              # Bot utilities
│   │   └── main.py             # Bot entry point
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── infrastructure/            # Infrastructure as Code
│   ├── nginx/
│   │   ├── default.conf        # Nginx configuration
│   │   ├── ssl/              # SSL certificates
│   │   └── Dockerfile
│   │
│   ├── redis/
│   │   └── redis.conf
│   │
│   ├── monitoring/
│   │   ├── prometheus/
│   │   └── grafana/
│   │
│   └── docker-compose/
│       ├── base.yml          # Base services (postgres, redis)
│       ├── development.yml   # Development overrides
│       ├── production.yml    # Production overrides
│       └── testing.yml       # Testing overrides
│
├── scripts/                  # Development/ops scripts
│   ├── setup.sh
│   ├── migrate.sh
│   ├── seed.sh
│   └── deploy.sh
│
├── docs/
│   ├── architecture/
│   ├── api/
│   └── development/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. Folder Responsibilities

### Backend - Presentation Layer (`app/api/v1/`)
| Folder | Responsibility |
|--------|--------------|
| `admin/` | Admin-only endpoints, RBAC enforcement, audit access |
| `auth/` | Login, logout, token refresh, password reset |
| `health/` | Health checks, metrics, readiness probes |
| `market/` | Market data queries (assets, pairs, candles) |
| `notifications/` | Notification CRUD, delivery status |
| `portfolio/` | Portfolio, snapshots, positions, trades |
| `risk/` | Risk validation, profile management, events |
| `trading/` | Orders, signals, paper trading, strategies |
| `users/` | User profile, API key management |

### Backend - Application Layer (`app/services/`)
| Service | Responsibility |
|---------|-------------|
| `auth_service` | Authentication flow, token validation |
| `audit_service` | Audit log creation, queries |
| `exchange_service` | Exchange account CRUD, credential management |
| `health_service` | Health status aggregation, metrics export |
| `market_service` | Market data operations, candle queries |
| `notification_service` | Notification creation, delivery logic |
| `paper_trading_service` | Paper order execution, simulation |
| `portfolio_service` | Portfolio calculations, value tracking |
| `risk_service` | Risk validation, decision making |
| `signal_service` | Signal generation, management |
| `strategy_service` | Strategy CRUD, version management |
| `user_service` | User operations, role management |

### Backend - Domain Layer (`app/domain/`)
| Folder | Responsibility |
|--------|--------------|
| `entities/` | Core business objects (Strategy, Position, Order) |
| `value_objects/` | Immutable domain values (Money, Percentage, Symbol) |
| `events/` | Domain events (OrderCreated, SignalGenerated) |
| `services/` | Pure business logic (RiskValidator, PositionSizer) |

### Backend - Infrastructure Layer (`app/database/`, `app/integrations/`)
| Folder | Responsibility |
|--------|--------------|
| `models/` | SQLAlchemy ORM models (persistence concerns) |
| `repositories/` | Data access patterns, query builders |
| `integrations/` | External API clients, exchange adapters |
| `core/` | Cross-cutting concerns (config, security, logging) |

### Frontend - Feature Organization (`src/features/`)
| Folder | Responsibility |
|--------|--------------|
| `auth/` | Login/logout, auth state, guards |
| `trading/` | Order forms, signal display, execution |
| `portfolio/` | Portfolio view, snapshots, PnL charts |
| `market/` | Asset lists, charts, pair selectors |
| `risk/` | Risk profile, events, validation display |
| `admin/` | User management, audit logs, settings |

---

## 3. Module Boundaries

### Core Domain Boundaries
```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                         │
│  (API Routes) → Services → Repositories → Models                  │
├─────────────────────────────────────────────────────────────────┤
│                      Application Layer                          │
│  (Or use Cases) → Domain Services → Repositories                  │
├─────────────────────────────────────────────────────────────────┤
│                       Domain Layer                              │
│  (Entities, Value Objects, Domain Events) → Pure Business Logic   │
├─────────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                        │
│  (External Systems, Database, Messaging)                          │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency Rules
```
api/ → services/ → domain/ → NO DEPENDENCIES
api/ → schemas/
services/ → domain/, repositories/, integrations/
domain/ → NO DEPENDENCIES (pure business logic)
repositories/ → models/, database/
models/ → database/
integrations/ → core/
tasks/ → services/, integrations/
```

### Layer Interaction Patterns
- **Presentation → Application**: Dependency Injection, DTOs
- **Application → Domain**: Entities passed as parameters
- **Application → Infrastructure**: Repository interfaces (dependency inversion)
- **Domain → Infrastructure**: Events published, no direct dependencies

---

## 4. Future Module Structure

### Trading Engine Module (To be extracted)
```
backend/
├── trading-engine/
│   ├── app/
│   │   ├── engines/           # Signal-to-order engines
│   │   ├── executors/         # Exchange order executors
│   │   ├── validators/        # Pre-trade validators
│   │   └── services/          # Matching, routing logic
│   └── Dockerfile
```

### Market Data Engine Module (To be extracted)
```
backend/
├── market-data-engine/
│   ├── app/
│   │   ├── collectors/        # Market data collectors
│   │   ├── processors/        # Data transformation
│   │   ├── streams/           # WebSocket streams
│   │   └── storage/           # Time-series storage
│   └── Dockerfile
```

### Risk Engine Module (To be extracted)
```
backend/
├── risk-engine/
│   ├── app/
│   │   ├── policies/          # Risk policies (configurable)
│   │   ├── validators/        # Real-time validators
│   │   ├── monitors/          # Risk monitoring
│   │   └── alerter/           # Risk alerts
│   └── Dockerfile
```

### Portfolio Engine Module (To be extracted)
```
backend/
├── portfolio-engine/
│   ├── app/
│   │   ├── calculators/       # PnL, value calculations
│   │   ├── trackers/          # Position tracking
│   │   ├── snapshotters/      # Portfolio snapshots
│   │   └── reporters/         # Report generation
│   └── Dockerfile
```

### AI Market Intelligence Module (To be extracted)
```
backend/
├── ai-market-intelligence/
│   ├── app/
│   │   ├── collectors/        # News, social data collection
│   │   ├── nlp/               # News sentiment analysis
│   │   ├── classifiers/         # Event classification
│   │   └── summarizer/          # AI summaries
│   ├── models/                # ML models
│   └── notebooks/             # Research notebooks
```

### AI Agent System Module (To be extracted)
```
backend/
├── ai-agent-system/
│   ├── app/
│   │   ├── agents/            # Agent implementations
│   │   ├── strategies/        # Agent strategies
│   │   ├── memory/            # Agent memory store
│   │   ├── tasks/             # Agent tasks
│   │   └── supervision/       # Multi-agent supervision
│   ├── engines/              # Agent execution engines
│   └── tools/                # Agent tools/integrations
```

---

## 5. Development Roadmap

### Phase 1: Foundation (2-3 weeks)
- [ ] Core domain entities and value objects
- [ ] Repository pattern refactoring
- [ ] Comprehensive test coverage (>80%)
- [ ] Docker production configuration
- [ ] CI/CD pipeline setup

### Phase 2: Security & Scale (3-4 weeks)
- [ ] RBAC implementation (roles, permissions)
- [ ] httpOnly cookie authentication
- [ ] Pagination for all list endpoints
- [ ] Redis caching layer
- [ ] Rate limiting middleware

### Phase 3: Real-time Features (2-3 weeks)
- [ ] WebSocket for market data
- [ ] Real-time notifications
- [ ] Event-driven architecture
- [ ] Live portfolio updates

### Phase 4: Multi-Exchange (3-4 weeks)
- [ ] Exchange adapter pattern
- [ ] Unified order routing
- [ ] Exchange account management
- [ ] Cross-exchange arbitrage foundation

### Phase 5: AI Integration (4-6 weeks)
- [ ] Market intelligence pipeline
- [ ] Basic signal generation agents
- [ ] Risk-adjusted strategy agents
- [ ] Telegram bot integration

### Phase 6: Production Harden (2-3 weeks)
- [ ] Monitoring & alerting
- [ ] Load testing
- [ ] Chaos engineering
- [ ] Documentation complete

---

## 6. Scalability Considerations

### Database Scaling
| concern | Strategy |
|---------|----------|
| **Millions of records** | Partitioning by date/user, read replicas |
| **High write volume** | Connection pooling, bulk inserts |
| **Complex queries** | Materialized views, read model separation |

### API Scaling
| concern | Strategy |
|---------|----------|
| **Thousands of users** | Horizontal scaling, load balancing |
| **Real-time data** | WebSocket connection pooling |
| **Caching** | Redis for hot data, CDN for static |

### Task Scaling
| concern | Strategy |
|---------|----------|
| **Background jobs** | Dedicated worker pools per domain |
| **Market data** | Distributed collectors, message queues |
| **AI processing** | GPU-enabled workers, async inference |

### Frontend Scaling
| concern | Strategy |
|---------|----------|
| **Bundle size** | Code splitting, lazy loading |
| **Data rendering** | Virtualization, pagination |
| **State management** | Selective subscriptions, normalization |

### Infrastructure Scaling
| concern | Strategy |
|---------|----------|
| **High availability** | Multi-region deployment |
| **Auto-scaling** | Kubernetes HPA, queue-based scaling |
| **Monitoring** | Prometheus metrics, distributed tracing |