# Folder Naming Rules

## 1. Fundamental Naming Principles

All naming follows the concept of **ubiquitous language**: names convey domain meaning directly, not technical implementation details.

## 2. Python Module/Folder Naming

### 2.1 Bounded Context Names
Use descriptive business capability names in `snake_case`:

```yaml
good: [trading, market_data, portfolio, risk_management, analysis]
bad:  [orders, data, port, analysis_service, risk_mgr]
```

### 2.2 Entity Module Names
Named after the aggregate root entity in `snake_case`:

```
domain/entities/
  trade.py          # Trade entity
  order.py          # Order entity (belongs to OrderAggregate)
  portfolio.py      # Portfolio aggregate root
  position.py       # Position (part of Portfolio aggregate)
```

**Rule**: If entity is part of an aggregate, prefix with aggregate name optionally

```
domain/entities/
  order.py              # Generic order
  # or if specifically Portfolio aggregate:
  portfolio_order.py    # Order within portfolio context
```

### 2.3 Value Object Module Names
Named after the concept they represent:

```
domain/value_objects/
  price.py
  quantity.py
  symbol.py
  currency.py
  timestamp.py
  order_side.py
  order_type.py
  order_status.py
  timeframe.py
```

### 2.4 Domain Service Names
Verb-first, describing service purpose:

```
domain/domain_services/
  risk_calculation.py          # Describes what it does
  portfolio_rebalancing.py
  order_matching.py
  market_analysis.py
```

### 2.5 Repository Interfaces
Named `<entity>_repository.py`:

```
domain/repositories/
  order_repository.py
  position_repository.py
  portfolio_repository.py
  market_data_repository.py
  strategy_repository.py
```

### 2.6 Infrastructure Implementations
Named `<implementation_type>_<entity>_repository.py`:

```
infrastructure/repositories/
  sqlalchemy_order_repository.py      # Technology + Entity
  redis_market_data_cache.py         # Technology + Domain
  ccxt_exchange_adapter.py           # Technology + Domain
  gemini_ai_provider.py              # Provider name + Domain
```

### 2.7 Use Cases
Use command/query naming pattern:

```
application/use_cases/commands/
  place_order.py
  cancel_order.py
  execute_strategy.py
  rebalance_portfolio.py

application/use_cases/queries/
  get_portfolio.py
  get_trade_history.py
  get_performance.py
```

### 2.8 Service Orchestrators
Named by responsibility:

```
application/services/
  trading_service.py
  market_data_service.py
  risk_monitoring_service.py
  strategy_service.py
  notification_service.py
```

### 2.9 Event Handlers
Named by event type they handle:

```
application/event_handlers/
  order_event_handlers.py      # Handles OrderCreated, OrderFilled, etc.
  trade_event_handlers.py      # Handles TradeExecuted
  risk_event_handlers.py       # Handles RiskLimitBreached
  notification_event_handlers.py
```

### 2.10 Domain Events
Named in past tense:

```
domain/events/
  order_created.py       # Contains OrderCreated class
  order_executed.py      # Contains OrderExecuted class
  trade_completed.py     # Contains TradeExecuted class
  risk_breached.py       # Contains RiskLimitBreached class
```

*Alternative flat structure*:
```
domain/events/
  order_events.py        # All order events
  trade_events.py        # All trade events
  portfolio_events.py    # All portfolio events
  risk_events.py         # All risk events
```

## 3. Pydantic Model / DTO Naming

### 3.1 Request Models
Named with `Request` suffix:

```python
class PlaceOrderRequest(BaseModel):
    ...

class GetPortfolioRequest(BaseModel):
    ...

class ExecuteStrategyRequest(BaseModel):
    ...
```

### 3.2 Response Models
Named with `Response` suffix:

```python
class PlaceOrderResponse(BaseModel):
    order_id: UUID
    status: OrderStatus

class PortfolioResponse(BaseModel):
    total_value: Decimal
    positions: list[PositionDto]

class TradeHistoryResponse(BaseModel):
    trades: list[TradeDto]
    pagination: PaginationInfo
```

### 3.3 DTOs (Data Transfer Objects)
Named with `Dto` suffix when transforming domain objects:

```python
class OrderDto(BaseModel):
    id: UUID
    symbol: str
    side: OrderSide
    quantity: Decimal

class TradeDto(BaseModel):
    id: UUID
    symbol: str
    price: Decimal
    quantity: Decimal
```

*Prefer inline response schemas over separate DTO classes for simple cases*

### 3.4 Query Parameters
Named clearly without abbreviations:

```python
class TradeHistoryQueryParams(BaseModel):
    symbol: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 100
    offset: int = 0
    order_by: str = "executed_at"
    order_dir: str = "desc"
```

## 4. Test File Naming

### 4.1 Unit Tests
Named `test_<module_name>.py` — mirrors source structure:

```
tests/unit/
  domain/
    test_entities.py          # tests domain/entities/
    test_value_objects.py     # tests domain/value_objects/
    test_domain_services.py   # tests domain/domain_services/

  application/
    test_place_order.py       # tests application/use_cases/commands/place_order.py
    test_get_portfolio.py     # tests application/use_cases/queries/get_portfolio.py
    test_trading_service.py   # tests application/services/trading_service.py

  infrastructure/
    test_order_repository.py  # tests infrastructure/repositories/order_repository.py
    test_redis_cache.py       # tests infrastructure/cache/redis_cache.py
```

### 4.2 Integration Tests
Named `test_<feature>_integration.py` or grouped by endpoint:

```
tests/integration/
  test_api_trading.py
  test_api_portfolio.py
  test_database_repositories.py
  test_exchange_connectivity.py
  test_websocket_streaming.py
```

### 4.3 E2E Tests
Named by workflow:

```
tests/e2e/
  test_order_placement_workflow.py
  test_portfolio_reporting_workflow.py
  test_risk_alert_workflow.py
```

## 5. Configuration File Naming

### 5.1 Environment Files
Strict naming convention:

```
.env                      # NEVER commit - actual secrets
.env.example              # Commit - template
.env.development          # Local development overrides
.env.testing              # Test environment
.env.staging              # Staging environment (future)
.env.production           # Production environment
```

### 5.2 Feature Flags / Settings
Use descriptive names:

```
config/
  exchanges/
    binance.yaml
    coinbase.yaml
    kraken.yaml

  strategies/
    default.yaml
    custom_ma_crossover.yaml

  ai_prompts/
    market_analysis.txt
    risk_assessment.txt
    trade_reporting.txt
```

## 6. Docker and Deployment Naming

### 6.1 Docker Compose Services
Named by service purpose:

```yaml
services:
  nginx:           # Reverse proxy
  api:             # FastAPI application
  celery_worker:   # Background tasks (future)
  postgres:        # Database
  redis:           # Cache
  minio:           # Object storage (future)
```

### 6.2 Docker Networks
Named by project prefix:

```yaml
networks:
  quantx-net:     # Primary application network
  quantx-db-net:  # Database-only network
```

### 6.3 Docker Volumes
Named by concern:

```
volumes:
  quantx-postgres-data:    # PostgreSQL persistence
  quantx-redis-data:       # Redis persistence
  quantx-uploads:          # Report uploads
  quantx-logs:             # Application logs
```

### 6.4 Environment Variables
Use UPPER_SNAKE_CASE with project prefix:

```bash
QUANTX_ENV=production
QUANTX_LOG_LEVEL=INFO
QUANTX_DATABASE_URL=postgresql+asyncpg://...
QUANTX_REDIS_URL=redis://redis:6379/0
QUANTX_TELEGRAM_BOT_TOKEN=...
QUANTX_GEMINI_API_KEY=...
QUANTX_OPENROUTER_API_KEY=...
QUANTX_SECRET_KEY=...
```

**Prefix rule**: All env vars MUST start with `QUANTX_` to avoid collision.

## 7. Frontend Naming Conventions

### 7.1 React Components
PascalCase for components:

```typescript
components/
  OrderForm.tsx           # Form component
  OrderBook.tsx           # Display component
  TradeHistoryTable.tsx   # Complex component
  PriceTicker.tsx         # Simple component
```

### 7.2 React Hooks
camelCase with `use` prefix:

```typescript
hooks/
  useMarketData.ts            # Custom hook for market data
  usePortfolio.ts             # Custom hook for portfolio data
  useWebSocket.ts             # WebSocket connection hook
  useAuth.ts                  # Authentication hook
  useTrading.ts               # Trading operations hook
```

### 7.3 Page Components
Named by feature or route:

```typescript
pages/
  Dashboard.tsx
  Trading.tsx
  Portfolio.tsx
  Strategies.tsx
  Analytics.tsx
  Settings.tsx
  Login.tsx
```

### 7.4 API Client Functions
camelCase, verb-first:

```typescript
api/
  fetchTrades()
  placeOrder()
  getPortfolio()
  streamMarketData()
```

### 7.5 TypeScript Types
PascalCase for types/interfaces, camelCase for values:

```typescript
types/
  Order.ts        # interface Order { ... }
  Trade.ts        # interface Trade { ... }
  Portfolio.ts    # interface Portfolio { ... }
  OrderSide.ts    # type OrderSide = 'BUY' | 'SELL'
```

## 8. Git and Branch Naming

### 8.1 Branch Naming
```
feature/<description>    # New features
bugfix/<description>     # Bug fixes
hotfix/<description>     # Production hotfixes
refactor/<description>   # Code refactoring
chore/<description>      # Maintenance tasks
docs/<description>       # Documentation only
```

### 8.2 Commit Message Format
Follow Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance
- `ci`: CI/CD changes

**Scope options**:
- `domain`, `application`, `infrastructure`, `presentation`
- `trading`, `portfolio`, `market-data`, `risk`, `ai`

**Examples**:
```
feat(trading): add support for stop-loss orders
fix(portfolio): calculate unrealized PnL correctly for short positions
refactor(domain): extract price validation logic into value object
docs(api): document new trading endpoints
```

## 9. Alphabetical Ordering

Within module `__init__.py` files and similar aggregators, list exports alphabetically:

```python
# domain/entities/__init__.py
from .order import Order
from .portfolio import Portfolio
from .position import Position
from .strategy import Strategy
from .trade import Trade

__all__ = ["Order", "Portfolio", "Position", "Strategy", "Trade"]
```

## 10. Special Naming Patterns

### 10.1 Factory Pattern
Names indicate purpose:
- `order_factory.py` - Creates orders from external data
- `ccxt_adapter_factory.py` - Creates exchange adapters
- `event_factory.py` - Creates domain events

### 10.2 Builder Pattern
Names indicate what they build:
- `order_builder.py` - Fluent interface for building orders
- `query_builder.py` - Dynamic query construction

### 10.3 Strategy Pattern
Names indicate strategy type:
- `market_making_strategy.py`
- `dca_strategy.py`
- `momentum_strategy.py`

### 10.4 Middleware/Auth
Prefix with concern:
- `auth_middleware.py`
- `telegram_auth_middleware.py`
- `rate_limit_middleware.py`
- `logging_middleware.py`

### 10.5 Constants
UPPER_SNAKE_CASE, grouped by domain:

```python
# domain/value_objects/price.py
MIN_PRICE = Decimal("0.00000001")
MAX_PRICE = Decimal("999999999.99999999")
PRICE_PRECISION = 8

# infrastructure/exchanges/ccxt_adapter.py
DEFAULT_TIMEOUT = 30000  # 30 seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2.0
```

## 11. Prohibited Naming Patterns

| Pattern | Reason | Example (Bad) | Preferred |
|---------|--------|---------------|-----------|
| Generic names | No semantic meaning | `utils.py`, `helpers.py`, `misc.py` | `trading_utils.py` or inline in use case |
| Hungarian notation | Legacy, not Pythonic | `str_symbol`, `int_quantity` | `Symbol`, `Quantity` |
| Abbreviations | Obscure meaning | `ord`, `pos`, `pf` | `order`, `position`, `portfolio` |
| Implementation detail in name | Violates encapsulation | `sqlalchemy_order_repository.py` in domain | `order_repository.py` in domain |
| "Manager" suffix | God object indicator | `OrderManager`, `TradeManager` | `OrderService`, `TradeOrchestrator` |
| "Handler" suffix (overused) | Misuse of pattern | `OrderHandler` in domain | Descriptive: `RiskAssessmentHandler` in infrastructure |
| Single-letter names | Unreadable | `o`, `p`, `t` | `order`, `portfolio`, `trade` |

## 12. Naming Consistency Matrix

| Concept | Python Class | Python File | Variable | Function/Method |
|---------|-------------|-------------|----------|-----------------|
| Entity | `Trade` | `trade.py` | `trade` | `get_trade()`, `save_trade()` |
| Value Object | `Price` | `price.py` | `price` | `create_price()` |
| Repository | `OrderRepository` | `order_repository.py` | `order_repo` | `save_order()` |
| Service | `RiskCalculationService` | `risk_calculation.py` | `risk_service` | `calculate_var()` |
| Use Case | `PlaceOrderUseCase` | `place_order.py` | `place_order_uc` | `execute()` |
| Event | `OrderCreated` | `order_created.py` | `event` | `publish()` |
| Model (ORM) | `SqlAlchemyOrder` | `trade_model.py` | `model` | (auto-generated) |
| Schema (Pydantic) | `PlaceOrderRequest` | `schemas.py` | `request` | - |
