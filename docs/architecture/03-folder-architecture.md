# Folder Architecture

## Monorepo Structure Overview

```
quantx-ai/
+-- backend/
¦   +-- app/
¦       +-- domain/
¦       ¦   +-- entities/
¦       ¦   +-- value_objects/
¦       ¦   +-- services/
¦       ¦   +-- events/
¦       ¦   +-- repositories/
¦       ¦   +-- exceptions/
¦       +-- application/
¦       ¦   +-- use_cases/
¦       ¦   +-- services/
¦       ¦   +-- commands/
¦       ¦   +-- queries/
¦       ¦   +-- dtos/
¦       +-- infrastructure/
¦       ¦   +-- database/
¦       ¦   ¦   +-- repositories/
¦       ¦   ¦   +-- migrations/
¦       ¦   ¦   +-- models/
¦       ¦   +-- cache/
¦       ¦   ¦   +-- redis/
¦       ¦   ¦   +-- strategies/
¦       ¦   +-- exchanges/
¦       ¦   ¦   +-- ccxt/
¦       ¦   ¦   +-- adapters/
¦       ¦   +-- ai/
¦       ¦   ¦   +-- gemini/
¦       ¦   ¦   +-- openrouter/
¦       ¦   +-- messaging/
¦       ¦       +-- telegram/
¦       ¦       +-- notifications/
¦       +-- presentation/
¦           +-- api/
¦           ¦   +-- v1/
¦           ¦   ¦   +-- trading/
¦           ¦   ¦   +-- portfolio/
¦           ¦   ¦   +-- market_data/
¦           ¦   +-- dependencies.py
¦           +-- websocket/
¦           ¦   +-- handlers/
¦           ¦   +-- managers/
¦           +-- bot/
¦               +-- handlers/
¦               +-- keyboards/
¦               +-- middlewares/
+-- frontend/
¦   +-- src/
¦       +-- components/
¦       ¦   +-- layout/
¦       ¦   +-- trading/
¦       ¦   +-- portfolio/
¦       ¦   +-- common/
¦       +-- hooks/
¦       +-- pages/
¦       +-- stores/
¦       +-- api/
¦       +-- types/
¦       +-- utils/
+-- infrastructure/
¦   +-- docker/
¦   ¦   +-- backend.Dockerfile
¦   ¦   +-- frontend.Dockerfile
¦   ¦   +-- docker-compose.yml
¦   +-- nginx/
¦   ¦   +-- nginx.conf
¦   +-- github-workflows/
¦       +-- ci.yml
¦       +-- cd.yml
+-- docs/
¦   +-- architecture/
+-- tests/
    +-- unit/
    +-- integration/
    +-- e2e/
```

## Backend Architecture Tree

### Domain Layer (app/domain/)
- entities/: Core business objects (Order, Position, Portfolio, Strategy, MarketData, User)
- value_objects/: Immutable values (Symbol, Price, Quantity, Money, Timestamp)
- services/: Domain services with business logic (TradingEngine, RiskEvaluator)
- events/: Domain events (OrderPlaced, PositionUpdated, RiskTriggered)
- repositories/: Repository interfaces (abstract definitions only)
- exceptions/: Domain-specific exceptions

### Application Layer (app/application/)
- use_cases/: Application workflows (ExecuteTrade, CalculatePortfolio, GenerateSignal)
- services/: Application orchestration services
- commands/: Command handlers (PlaceOrderCommand, CancelOrderCommand)
- queries/: Query handlers (GetPortfolioQuery, GetTradeHistoryQuery)
- dtos/: Data transfer objects for API boundaries

### Infrastructure Layer (app/infrastructure/)
- database/: SQLAlchemy implementations, migrations, models
- cache/: Redis clients, caching strategies
- exchanges/: CCXT wrappers, exchange-specific adapters
- ai/: Gemini, OpenRouter clients, prompt management
- messaging/: Telegram client, notification dispatchers

### Presentation Layer (app/presentation/)
- api/: FastAPI routers, dependency injection, route handlers
- websocket/: WebSocket handlers, connection managers
- bot/: aiogram handlers, keyboards, middlewares

## Frontend Architecture Tree

### Components (frontend/src/components/)
- layout/: Shell components (Header, Sidebar, Layout)
- trading/: Trading-specific UI (OrderForm, PositionTable, TradeHistory)
- portfolio/: Portfolio visualization (PortfolioSummary, AllocationChart)
- common/: Shared UI primitives (Button, Modal, Loading)

### State Management (frontend/src/stores/)
- trading-store.ts: Trading state, orders, positions
- portfolio-store.ts: Portfolio metrics, asset allocation
- auth-store.ts: User session, preferences

### Data Fetching (frontend/src/api/)
- client.ts: TanStack Query client configuration
- endpoints.ts: API endpoint definitions

## Infrastructure Architecture Tree

### Docker (infrastructure/docker/)
- backend.Dockerfile: Multi-stage Python build
- frontend.Dockerfile: Multi-stage Node build
- docker-compose.yml: Production orchestration

### Nginx (infrastructure/nginx/)
- nginx.conf: SSL termination, rate limiting, proxy config

### CI/CD (infrastructure/github-workflows/)
- ci.yml: Lint, test, build pipeline
- cd.yml: Deploy to VPS pipeline

## Shared Kernel
- Common value objects shared between layers
- Exception base classes
- Type definitions
- Utility functions
