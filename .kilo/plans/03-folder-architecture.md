# Folder Architecture

## 1. Project Root Structure

```
quantx-ai/
├── .kilo/
│   ├── plans/                          # Architecture plans (this sprint)
│   └── agents/                         # Kilo agent definitions
├── .github/
│   └── workflows/                      # CI/CD pipelines
├── backend/                            # Python FastAPI application
├── frontend/                           # React TypeScript application
├── docs/                               # Project documentation
│   ├── architecture/                   # Architecture documentation
│   ├── api/                            # API documentation (generated)
│   └── deployment/                     # Deployment runbooks
├── scripts/                            # Build/deploy scripts
├── tests/                              # Integration/E2E tests
├── .env.example                        # Environment template
├── .gitignore
├── docker-compose.yml                  # Production compose
├── docker-compose.dev.yml              # Development compose
├── README.md
└── ARCHITECTURE.md                     # Links to architecture docs
```

## 2. Backend Folder Structure

```
backend/
├── src/
│   ├── domain/                         # ▸ NEVER IMPORT ANYTHING FROM OUTSIDE
│   │   ├── __init__.py
│   │   ├── entities/                   # Business objects with identity
│   │   │   ├── __init__.py
│   │   │   ├── trade.py
│   │   │   ├── order.py
│   │   │   ├── position.py
│   │   │   ├── portfolio.py            # Aggregate root
│   │   │   └── strategy.py
│   │   │
│   │   ├── value_objects/              # Immutable value types
│   │   │   ├── __init__.py
│   │   │   ├── price.py
│   │   │   ├── quantity.py
│   │   │   ├── symbol.py
│   │   │   ├── currency.py
│   │   │   ├── timestamp.py            # Timezone-aware
│   │   │   └── order_side.py
│   │   │
│   │   ├── aggregates/                 # Consistency boundaries
│   │   │   ├── __init__.py
│   │   │   ├── portfolio_aggregate.py
│   │   │   └── order_aggregate.py
│   │   │
│   │   ├── domain_services/            # Complex business logic
│   │   │   ├── __init__.py
│   │   │   ├── risk_calculation.py
│   │   │   ├── portfolio_rebalancing.py
│   │   │   ├── order_matching.py
│   │   │   └── market_analysis.py
│   │   │
│   │   ├── repositories/               # INTERFACES ONLY (ports)
│   │   │   ├── __init__.py
│   │   │   ├── order_repository.py
│   │   │   ├── position_repository.py
│   │   │   ├── portfolio_repository.py
│   │   │   ├── market_data_repository.py
│   │   │   ├── strategy_repository.py
│   │   │   └── trade_repository.py
│   │   │
│   │   └── events/                     # Domain events
│   │       ├── __init__.py
│   │       ├── order_events.py
│   │       ├── trade_events.py
│   │       ├── portfolio_events.py
│   │       └── risk_events.py
│   │
│   ├── application/                    # Use cases & orchestration
│   │   ├── __init__.py
│   │   ├── use_cases/                  # Command/Query handlers
│   │   │   ├── __init__.py
│   │   │   ├── commands/               # Write operations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── place_order.py
│   │   │   │   ├── cancel_order.py
│   │   │   │   ├── close_position.py
│   │   │   │   ├── execute_strategy.py
│   │   │   │   ├── update_settings.py
│   │   │   │   └── rebalance_portfolio.py
│   │   │   │
│   │   │   └── queries/                # Read operations
│   │   │       ├── __init__.py
│   │   │       ├── get_portfolio.py
│   │   │       ├── get_trade_history.py
│   │   │       ├── get_market_analysis.py
│   │   │       ├── get_performance.py
│   │   │       └── get_open_orders.py
│   │   │
│   │   ├── services/                   # Orchestration services
│   │   │   ├── __init__.py
│   │   │   ├── trading_service.py      # High-level trading operations
│   │   │   ├── market_data_service.py  # Data aggregation pipelines
│   │   │   ├── risk_monitoring_service.py
│   │   │   ├── strategy_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   ├── event_handlers/             # Domain event consumers
│   │   │   ├── __init__.py
│   │   │   ├── order_event_handlers.py
│   │   │   ├── trade_event_handlers.py
│   │   │   ├── risk_event_handlers.py
│   │   │   └── notification_event_handlers.py
│   │   │
│   │   ├── unit_of_work.py            # Transaction management
│   │   ├── event_bus.py               # Event publishing
│   │   └── exceptions.py              # Application-level exceptions
│   │
│   ├── infrastructure/                 # Implementation details
│   │   ├── __init__.py
│   │   │
│   │   ├── database/                   # Database concerns
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # SQLAlchemy session factory
│   │   │   ├── base.py                # Declarative base
│   │   │   ├── models/                # SQLAlchemy ORM models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── trade.py
│   │   │   │   ├── order.py
│   │   │   │   ├── position.py
│   │   │   │   ├── portfolio.py
│   │   │   │   └── market_data.py
│   │   │   └── migrations/            # Alembic migrations
│   │   │       └── versions/
│   │   │
│   │   ├── repositories/               # Repository IMPLEMENTATIONS
│   │   │   ├── __init__.py
│   │   │   ├── sqlalchemy_order_repository.py
│   │   │   ├── sqlalchemy_position_repository.py
│   │   │   ├── sqlalchemy_portfolio_repository.py
│   │   │   ├── sqlalchemy_market_data_repository.py
│   │   │   └── sqlalchemy_strategy_repository.py
│   │   │
│   │   ├── cache/                      # Caching implementations
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py
│   │   │   ├── market_data_cache.py
│   │   │   └── session_cache.py
│   │   │
│   │   ├── exchanges/                  # CCXT adapters
│   │   │   ├── __init__.py
│   │   │   ├── base_exchange.py       # Abstract base
│   │   │   ├── ccxt_adapter.py
│   │   │   ├── exchange_factory.py
│   │   │   └── rate_limiter.py         # Per-exchange rate limiting
│   │   │
│   │   ├── ai/                         # AI providers
│   │   │   ├── __init__.py
│   │   │   ├── base_ai_provider.py    # Abstract interface
│   │   │   ├── gemini_provider.py
│   │   │   ├── openrouter_provider.py
│   │   │   └── ai_router.py           # Failover logic
│   │   │
│   │   ├── messaging/                  # Notifications
│   │   │   ├── __init__.py
│   │   │   ├── telegram_bot.py
│   │   │   ├── notification_handler.py
│   │   │   └── message_templates.py
│   │   │
│   │   ├── websocket/                  # WebSocket infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── connection_manager.py
│   │   │   └── market_data_stream.py
│   │   │
│   │   ├── di/                         # Dependency injection
│   │   │   ├── __init__.py
│   │   │   └── container.py            # DIContainer configuration
│   │   │
│   │   ├── security/                   # Security implementations
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # JWT, Telegram auth
│   │   │   ├── encryption.py          # Data encryption
│   │   │   └── rate_limiter.py         # API rate limiting
│   │   │
│   │   └── config/                     # Configuration loading
│   │       ├── __init__.py
│   │       ├── settings.py            # Pydantic Settings
│   │       ├── database.py
│   │       └── redis.py
│   │
│   └── presentation/                   # User interfaces
│       ├── __init__.py
│       │
│       ├── api/                        # REST API
│       │   ├── __init__.py
│       │   ├── dependencies.py         # FastAPI dependencies
│       │   ├── middleware.py           # Custom middleware
│       │   │
│       │   ├── v1/                     # API versioning
│       │   │   ├── __init__.py
│       │   │   ├── router.py           # Main router
│       │   │   ├── trading/            # Trading endpoints
│       │   │   │   ├── __init__.py
│       │   │   │   ├── router.py
│       │   │   │   └── schemas.py      # Request/Response DTOs
│       │   │   ├── portfolio/          # Portfolio endpoints
│       │   │   │   ├── __init__.py
│       │   │   │   ├── router.py
│       │   │   │   └── schemas.py
│       │   │   ├── market_data/        # Market data endpoints
│       │   │   │   ├── __init__.py
│       │   │   │   ├── router.py
│       │   │   │   └── schemas.py
│       │   │   └── system/             # System endpoints
│       │   │       ├── __init__.py
│       │   │       ├── router.py
│       │   │       └── schemas.py
│       │   └── └──
│       │
│       ├── telegram/                   # Telegram bot
│       │   ├── __init__.py
│       │   ├── bot.py                  # aiogram bot setup
│       │   ├── handlers.py             # Message handlers
│       │   ├── keyboards.py            # Inline/keyboard markups
│       │   ├── middlewares.py          # Auth, logging
│       │   └── keyboards.py
│       │
│       ├── websocket/                  # WebSocket handlers
│       │   ├── __init__.py
│       │   ├── handlers.py             # Connection handlers
│       │   └── protocols.py            # Message protocols
│       │
│       └── dto/                        # Data transfer objects (alternative location)
│           └── (moved to endpoint-specific schemas)
│
├── tests/                              # Backend tests
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── unit/                          # Unit tests (fast, isolated)
│   │   ├── __init__.py
│   │   ├── domain/                    # Domain logic tests
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_domain_services.py
│   │   ├── application/               # Use case tests
│   │   │   ├── test_place_order.py
│   │   │   └── test_portfolio_service.py
│   │   └── infrastructure/            # Infrastructure tests
│   │       ├── test_repositories.py
│   │       └── test_cache.py
│   │
│   ├── integration/                   # Integration tests (slower)
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_exchange_connectivity.py
│   │
│   └── e2e/                          # End-to-end tests
│       ├── __init__.py
│       └── test_trading_workflows.py
│
├── alembic/                           # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── scripts/                           # Utility scripts
│   ├── init_db.py                     # Initialize database
│   ├── seed_data.py                   # Seed test data
│   ├── run_backtest.py                # Execute backtests
│   └── health_check.py                # System health check
│
├── pyproject.toml                     # Project metadata & deps
├── .env
├── .env.example
└── Dockerfile
```

## 3. Frontend Folder Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   ├── manifest.json
│   └── robots.txt
│
├── src/
│   ├── api/                           # API client layer
│   │   ├── client.ts                  # Axios/fetch config
│   │   ├── endpoints.ts               # API endpoint URLs
│   │   ├── trading.ts                 # Trading API calls
│   │   ├── portfolio.ts               # Portfolio API calls
│   │   ├── market-data.ts             # Market data API calls
│   │   └── websocket.ts               # WebSocket client
│   │
│   ├── components/                    # Reusable UI components
│   │   ├── ui/                        # Base UI (following shadcn/ui patterns)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layout/                    # Layout components
│   │   │   ├── header.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── footer.tsx
│   │   │   └── shell.tsx
│   │   ├── trading/                   # Trading-specific components
│   │   │   ├── order-form.tsx
│   │   │   ├── order-book.tsx
│   │   │   ├── trade-history.tsx
│   │   │   └── position-card.tsx
│   │   ├── portfolio/                 # Portfolio components
│   │   │   ├── balance-card.tsx
│   │   │   ├── allocation-chart.tsx
│   │   │   └── pnl-chart.tsx
│   │   └── market/                    # Market data components
│   │       ├── price-ticker.tsx
│   │       ├── candlestick-chart.tsx
│   │       └── market-overview.tsx
│   │
│   ├── pages/                         # Route pages (Next.js style)
│   │   ├── dashboard.tsx              # Main dashboard
│   │   ├── trading.tsx                # Trading interface
│   │   ├── portfolio.tsx              # Portfolio overview
│   │   ├── strategies.tsx             # Strategy management
│   │   ├── analytics.tsx              # Analytics & reports
│   │   ├── settings.tsx               # User settings
│   │   └── login.tsx                  # Auth page (if needed)
│   │
│   ├── hooks/                         # Custom React hooks
│   │   ├── useWebSocket.ts
│   │   ├── useMarketData.ts
│   │   ├── usePortfolio.ts
│   │   ├── useTrading.ts
│   │   └── useAuth.ts
│   │
│   ├── stores/                        # State management (TanStack Query)
│   │   ├── trading.ts                 # Trading-related queries/mutations
│   │   ├── portfolio.ts               # Portfolio queries/mutations
│   │   ├── market-data.ts             # Market data queries (cached)
│   │   └── user.ts                    # User state
│   │
│   ├── lib/                           # Core utilities
│   │   ├── utils.ts                   # General utilities
│   │   ├── constants.ts               # App constants
│   │   ├── types.ts                   # TypeScript type definitions
│   │   ├── formatters.ts              # Number, date formatting
│   │   └── validators.ts              # Form validators
│   │
│   ├── styles/                        # Global styles
│   │   ├── globals.css
│   │   └── tailwind.css
│   │
│   ├── App.tsx                        # Root component
│   ├── main.tsx                       # Entry point
│   └── vite-env.d.ts
│
├── tests/                             # Frontend tests
│   ├── unit/
│   │   └── components.test.tsx
│   ├── integration/
│   │   └── api.test.ts
│   └── e2e/
│       └── app.test.ts
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── index.html
```

## 4. Shared Resources

```
# Future consideration: shared types/contracts
shared/
├── contracts/                         # API contracts (OpenAPI spec)
│   └── openapi.yaml
├── types/                             # Shared TypeScript/Python types
│   └── (for future code generation)
└── docs/                              # Shared architecture docs
```

## 5. Documentation Structure

```
docs/
├── architecture/
│   ├── 00-overview.md
│   ├── 01-layer-architecture.md
│   ├── 02-folder-architecture.md
│   ├── 03-module-architecture.md
│   ├── ... (all 20 architecture documents)
│   └── README.md
├── api/
│   ├── openapi.json
│   ├── openapi.yaml
│   └── endpoints.md
├── deployment/
│   ├── vps-setup.md
│   ├── docker-deployment.md
│   ├── ssl-setup.md
│   └── backup-restore.md
└── operations/
    ├── monitoring.md
    ├── troubleshooting.md
    └── runbooks/
```

## 6. Configuration Files

```
config/
├── defaults.yaml                      # Default configuration
├── exchanges/                         # Exchange-specific configs
│   ├── binance.yaml
│   ├── coinbase.yaml
│   └── kraken.yaml
├── strategies/                        # Strategy configurations
│   ├── default.yaml
│   └── custom/
└── prompts/                           # AI prompt templates
    ├── market_analysis.txt
    ├── risk_assessment.txt
    └── report_generation.txt
```

## 7. Folder Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Domain noun | `snake_case` | `trade`, `portfolio_aggregate` |
| Module/package | `snake_case` | `trading`, `market_data` |
| Handler/Service | `snake_case` | `place_order.py`, `risk_service.py` |
| Test file | `test_<module>.py` | `test_order.py` |
| FastAPI router | `<resource>.py` | `trading.py`, `portfolio.py` |
| React component | `PascalCase` | `OrderForm.tsx` |
| React hook | `use<Feature>`.ts` | `useMarketData.ts` |

## 8. Module Internal Structure

All Python modules follow this structure:

```python
"""Module docstring explaining purpose."""

# 1. Standard library imports
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import AsyncIterator

# 2. Third-party imports
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application imports (domain first, then others)
from src.domain.entities import Order
from src.domain.value_objects import Price
from src.domain.repositories import OrderRepository
from src.application.exceptions import OrderNotFoundError

# 4. Module-level constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# 5. Type definitions
OrderFilters = dict[str, Any]

# 6. Main implementation
class OrderService:
    """Business logic for order operations."""

    def __init__(self, repo: OrderRepository):
        self._repo = repo

    async def find_by_id(self, id: UUID) -> Order:
        ...

# 7. Helper/private functions
def _validate_order(order: Order) -> None:
    ...

# 8. Public API
__all__ = ["OrderService", "OrderFilters"]
```

## 9. Prohibited Cross-Layer Imports

```
❌ Domain imports Application
❌ Domain imports Infrastructure
❌ Domain imports Presentation
❌ Application imports Infrastructure directly (use interfaces)
❌ Application imports Presentation
❌ Infrastructure imports Presentation
❌ Any layer imports from outer layer
```

**Allowed imports between layers**:

```
✅ Application imports Domain
✅ Infrastructure imports Domain (to implement interfaces) AND Application
✅ Presentation imports Application (to call use cases)
```

## 10. Module Grouping by Feature

Features are grouped by business capability, not technical layer:

```
backend/src/domain/
├── trading/           # All trading-related domain logic
│   ├── entities/
│   ├── value_objects/
│   ├── services/
│   └── repositories/
├── market_data/       # All market data domain logic
├── portfolio/         # Portfolio and risk domain logic
└── strategy/          # Strategy management domain logic
```

**Alternative (Smaller Projects)**:
Use flat structure with descriptive prefixes:
- `entities/trade.py`, `entities/order.py`
- `services/trading_service.py`, `services/market_service.py`
