# Package Dependency Rules

## 1. Dependency Direction Enforcement

The fundamental rule of Clean Architecture is enforced absolutely:

```
Domain ← Application ← Infrastructure ← Presentation
```

```
┌─────────────────────────────────────────────────────────────┐
│  Domain Layer: PURE                                         │
│  - No dependencies on anything outside this folder          │
│  - Imports only: stdlib, typing, __future__                │
│  - Defines interfaces but never implements external deps    │
└─────────────────────────────────────────────────────────────┘
                       ↑
                       │ (imports interfaces)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Application Layer: STRATEGY                                  │
│  - Imports only: Domain + stdlib                            │
│  - Defines use cases, orchestrates domain objects           │
│  - Never imports Infrastructure or Presentation              │
└─────────────────────────────────────────────────────────────┘
                       ↑
                       │ (implements interfaces)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer: DETAILS                                │
│  - Imports: Domain + Application + stdlib                   │
│  - Implements interfaces defined in Domain                  │
│  - Never imports Presentation                                │
└─────────────────────────────────────────────────────────────┘
                       ↑
                       │ (calls use cases)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer: ADAPTERS                                 │
│  - Imports: Application (and indirectly Domain)             │
│  - Translates between external formats and internal models  │
│  - Never imports Infrastructure (use DI container)           │
└─────────────────────────────────────────────────────────────┘
```

### Violation Detection

**At CI time**, import cycle and layer violation checks MUST run:

```bash
# Using griffe or pylint with custom rules
python -m pylint backend/src --disable=all --enable=wrong-import-position

# Using import-linter
import-linter enforce backend/src/import_linter.ini
```

## 2. Allowed Import Matrix

| From \ To | Domain | Application | Infrastructure | Presentation |
|-----------|--------|-------------|----------------|--------------|
| **Domain** | ✅ | ❌ | ❌ | ❌ |
| **Application** | ✅ | ❌ | ❌ | ❌ |
| **Infrastructure** | ✅ | ✅ | ❌ | ❌ |
| **Presentation** | ✅ | ✅ | ✅ | ❌ |
| **External Libs** | ✅ | ✅ | ✅ | ✅ |

**Legend**:
- ✅ = Allowed to import
- ❌ = Strictly forbidden
- External Libs = Any third-party imported in `__init__.py` (pydantic, sqlalchemy, aiohttp, etc.)

### Exception: Test Code
Tests in `tests/` may import from ANY layer to enable unit testing.

## 3. Fine-Grained Package Rules

### 3.1 Domain Package

```
backend/src/domain/
├── __init__.py
├── entities/
│   ├── __init__.py
│   ├── base_entity.py
│   ├── trade.py
│   ├── order.py
│   ├── position.py
│   ├── portfolio.py      # Aggregate root
│   └── strategy.py
│
├── value_objects/
│   ├── __init__.py
│   ├── base_value_object.py
│   ├── price.py
│   ├── quantity.py
│   ├── symbol.py
│   ├── currency.py
│   ├── timestamp.py
│   ├── order_side.py
│   ├── order_type.py
│   └── order_status.py
│
├── aggregates/
│   ├── __init__.py
│   ├── base_aggregate.py
│   ├── portfolio_aggregate.py
│   └── order_aggregate.py
│
├── domain_services/
│   ├── __init__.py
│   ├── risk_calculation.py
│   ├── portfolio_rebalancing.py
│   ├── order_matching.py
│   └── market_analysis.py
│
├── repositories/          # INTERFACES ONLY — no implementation
│   ├── __init__.py
│   ├── base_repository.py # ABC definition
│   ├── order_repository.py
│   ├── position_repository.py
│   ├── portfolio_repository.py
│   ├── market_data_repository.py
│   └── trade_repository.py
│
└── events/
    ├── __init__.py
    ├── base_event.py
    ├── order_events.py
    ├── trade_events.py
    ├── portfolio_events.py
    └── risk_events.py
```

**Allowed imports within domain**:
- `domain.*` → Any other `domain.*`
- `domain.*` → stdlib only

**Forbidden**:
- ❌ `domain.entities` imports `domain.repositories` (reverse dependency)
- ❌ `domain.value_objects` imports `domain.entities`
- ❌ Any `domain.*` imports from `application`, `infrastructure`, `presentation`

### 3.2 Application Package

```
backend/src/application/
├── __init__.py
├── use_cases/
│   ├── __init__.py
│   ├── base_use_case.py
│   ├── commands/            # Write operations (CQRS Commands)
│   │   ├── __init__.py
│   │   ├── place_order.py
│   │   ├── cancel_order.py
│   │   ├── close_position.py
│   │   ├── execute_strategy.py
│   │   ├── update_settings.py
│   │   └── rebalance_portfolio.py
│   └── queries/             # Read operations (CQRS Queries)
│       ├── __init__.py
│       ├── get_portfolio.py
│       ├── get_trade_history.py
│       ├── get_market_analysis.py
│       ├── get_performance.py
│       └── get_open_orders.py
│
├── services/               # Orchestration, not business logic
│   ├── __init__.py
│   ├── trading_service.py
│   ├── market_data_service.py
│   ├── risk_monitoring_service.py
│   ├── strategy_service.py
│   └── notification_service.py
│
├── event_handlers/
│   ├── __init__.py
│   ├── order_event_handlers.py
│   ├── trade_event_handlers.py
│   ├── risk_event_handlers.py
│   └── notification_event_handlers.py
│
├── unit_of_work.py
├── event_bus.py
└── exceptions.py
```

**Allowed imports within application**:
- `application.*` → Any `domain.*`
- `application.*` → Any other `application.*`

**Forbidden**:
- ❌ `application.use_cases` imports `infrastructure.*`
- ❌ `application.services` imports `infrastructure.*`
- ❌ Any `application.*` imports from `presentation`

### 3.3 Infrastructure Package

```
backend/src/infrastructure/
├── __init__.py
│
├── database/
│   ├── __init__.py
│   ├── session.py
│   ├── base.py
│   ├── models/            # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── trade.py
│   │   ├── order.py
│   │   ├── position.py
│   │   ├── portfolio.py
│   │   └── market_data.py
│   └── migrations/
│
├── repositories/          # IMPLEMENTATIONS of domain interfaces
│   ├── __init__.py
│   ├── sqlalchemy_order_repository.py
│   ├── sqlalchemy_position_repository.py
│   ├── sqlalchemy_portfolio_repository.py
│   ├── sqlalchemy_market_data_repository.py
│   └── sqlalchemy_strategy_repository.py
│
├── cache/
│   ├── __init__.py
│   ├── redis_client.py
│   ├── market_data_cache.py
│   └── session_cache.py
│
├── exchanges/
│   ├── __init__.py
│   ├── base_exchange.py
│   ├── ccxt_adapter.py
│   ├── exchange_factory.py
│   └── rate_limiter.py
│
├── ai/
│   ├── __init__.py
│   ├── base_ai_provider.py
│   ├── gemini_provider.py
│   ├── openrouter_provider.py
│   └── ai_router.py
│
├── messaging/
│   ├── __init__.py
│   ├── telegram_bot.py
│   ├── notification_handler.py
│   └── message_templates.py
│
├── websocket/
│   ├── __init__.py
│   ├── connection_manager.py
│   └── market_data_stream.py
│
├── di/
│   ├── __init__.py
│   └── container.py        # Wire everything together
│
├── security/
│   ├── __init__.py
│   ├── auth.py
│   ├── encryption.py
│   └── rate_limiter.py
│
└── config/
    ├── __init__.py
    ├── settings.py        # Pydantic Settings
    ├── database.py
    └── redis.py
```

**Allowed imports within infrastructure**:
- `infrastructure.*` → Any `domain.*`
- `infrastructure.*` → Any `application.*`
- `infrastructure.*` → Any other `infrastructure.*`

**Forbidden**:
- ❌ `infrastructure.database` imports `presentation.*`
- ❌ Any `infrastructure.*` imports from `presentation`

### 3.4 Presentation Package

```
backend/src/presentation/
├── __init__.py
│
├── api/
│   ├── __init__.py
│   ├── dependencies.py   # FastAPI dependencies
│   ├── middleware.py     # Auth, logging, error handling
│   └── v1/
│       ├── __init__.py
│       ├── router.py     # Main router aggregator
│       ├── trading/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── schemas.py  # Pydantic request/response models
│       ├── portfolio/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── schemas.py
│       ├── market_data/
│       │   ├── __init__.py
│       │   ├── router.py
│       │   └── schemas.py
│       └── system/
│           ├── __init__.py
│           ├── router.py
│           └── schemas.py
│
├── telegram/
│   ├── __init__.py
│   ├── bot.py
│   ├── handlers.py       # aiogram message/callback handlers
│   ├── keyboards.py      # Inline keyboards
│   └── middlewares.py
│
├── websocket/
│   ├── __init__.py
│   ├── handlers.py       # WebSocket connection handlers
│   └── protocols.py      # Message protocols
│
└── dto/                  # (Optional, alternative to endpoint schemas)
    └── (consolidated into endpoint schemas)
```

**Allowed imports within presentation**:
- `presentation.*` → Any `application.*`
- `presentation.*` → Any `presentation.*`
- `presentation.*` → `domain.*` (only for type hints, using `TYPE_CHECKING`)

**Forbidden**:
- ❌ `presentation.api` imports `infrastructure.*` directly
- ❌ Any `presentation.*` imports from `infrastructure`

## 4. Dependency Injection Container Architecture

The DI Container (`src/infrastructure/di/container.py`) is the SINGLE POINT where implementations are wired to interfaces.

```python
# DI Container structure (conceptual)
class Container:
    # Domain interfaces → Infrastructure implementations
    order_repository: OrderRepository = SQLAlchemyOrderRepository(session)
    portfolio_repository: PortfolioRepository = SQLAlchemyPortfolioRepository(session)
    market_data_repository: MarketDataRepository = SQLAlchemyMarketDataRepository(session)

    # Use cases
    place_order_use_case: PlaceOrderUseCase = PlaceOrderUseCase(...)
    get_portfolio_use_case: GetPortfolioUseCase = GetPortfolioUseCase(...)

    # External services
    gemini_ai: AIProvider = GeminiAIProvider()
    openrouter_ai: AIProvider = OpenRouterAIProvider()
    ai_router: AIRouter = AIRouter([gemini_ai, openrouter_ai])

    # Infrastructure
    telegram_bot: TeleBot = TeleBot(...)
    redis_client: RedisClient = RedisClient(...)
```

**Rules**:
1. Container defined ONLY in infrastructure layer
2. Shared as singleton across application lifetime
3. NEVER import Container directly in Presentation - use FastAPI `Depends()`
4. NEVER instantiate classes directly - always through DI

## 5. Communication Between Layers

### 5.1 Domain → Application
- **Mode**: Interface (Abstract Base Class)
- **Example**: `Application` calls `order_repo.save(order)`
- **Contract**: Defined in `domain.repositories`

### 5.2 Application → Infrastructure
- **Mode**: Dependency Injection
- **Example**: `UseCase.__init__(order_repo, portfolio_repo)`
- **Contract**: Implementations satisfy domain interfaces

### 5.3 Infrastructure → Domain
- **Mode**: Exception translation
- **Example**: `SQLAlchemyOrderRepository.save()` catches SQLAlchemy `IntegrityError` and re-raises as `DomainError`
- **Rule**: Infrastructure exceptions NEVER leak to application/domain

### 5.4 Presentation → Application
- **Mode**: Use case invocation
- **Example**: `place_order_use_case.execute(command)`
- **Contract**: Defined in `application.use_cases`

### 5.5 Presentation → Domain
- **Mode**: Type checking only (`if TYPE_CHECKING`)
- **Rule**: Never import domain objects at runtime in presentation
- **Exception**: DTO/schema definitions may reference domain enums

## 6. Dependency Versioning

All external dependencies managed via `pyproject.toml`.

```toml
# Core framework dependencies
fastapi = "^0.110.0"
sqlalchemy = "^2.0.0"
alembic = "^1.13.0"
pydantic = "^2.0.0"

# Data stores
asyncpg = "^0.29.0"         # PostgreSQL async driver
redis = {extras = ["hiredis"], version = "^5.0.0"}

# External integrations
ccxt = "^4.0.0"
aiogram = "^3.0.0"
google-generativeai = "^0.3.0"

# Utilities
python-dotenv = "^1.0.0"
python-json-logger = "^2.0.0"
tenacity = "^8.2.0"
```

## 7. Dependency Violation Prevention

### CI Enforcement (GitHub Actions)
```yaml
# .github/workflows/architecture-check.yml
jobs:
  dependency_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install import-linter
        run: pip install import-linter
      - name: Check layer dependencies
        run: lint-imports --config import_linter.ini
```

### Runtime Enforcement
- Python import hooks for development
- Fail-fast on import violations
- Clear error messages: "Domain layer must not import from Infrastructure layer"

## 8. Internal vs External Dependency Rules

### Internal Dependencies (Project2.registry.io)
Must be resolvable within the project's source layout (no registry call needed).

Pattern:
- An internal package shall `import` another using `src.` prefix when code is checked out, and shall `import` by bare package name when installed as an editable/packaged local artifact.
- Internal packages bump versions together (semver minor or patch) when any public interface changes.

Enforcement:
- The CI installs the repo in editable mode (`pip install -e .`) before test/lint, so the bare package import is validated.

### External Dependencies (PyPI)
```python
# Example of acceptable external dependency
# domain/value_objects/price.py
from decimal import Decimal  # stdlib - always OK

# infrastructure/database/models.py
from sqlalchemy import Column, Numeric  # external framework - OK in infrastructure

# domain/entities/trade.py
from pydantic import BaseModel  # ❌ WRONG - pydantic in domain?
# Instead use regular class with __init__
```

**Rule**: Only stdlib allowed in domain. All external frameworks in infrastructure.

## 9. Cross-Context Communication Rules

### 9.1 Via Domain Events
Preferred for eventual consistency and decoupling.

```python
# Order module publishes event
await self.event_bus.publish(OrderExecuted(trade=trade))

# Portfolio module listens
@event_handler(OrderExecuted)
async def on_order_executed(event: OrderExecuted):
    await self.update_position(event.trade)
```

### 9.2 Via Repository Interface
When direct database queries are needed across contexts.

```python
# In application layer (orchestration)
portfolio = await portfolio_repo.get_active()
orders = await order_repo.find_by_portfolio(portfolio.id)
```

### 9.3 Via Application Service Orchestration
When complex workflow spans multiple contexts.

```python
class ExecuteStrategyService:
    def __init__(
        self,
        analysis_repo: AnalysisRepository,    # analysis context
        order_use_case: PlaceOrderUseCase,    # trading context
        portfolio_repo: PortfolioRepository,  # portfolio context
        risk_service: RiskService,            # risk context
    ):
        ...

    async def execute(self, strategy: Strategy):
        analysis = await self.analysis_repo.find_latest(strategy.symbol)
        position = await self.portfolio_repo.get_position(strategy.symbol)
        risk_assessment = await self.risk_service.assess(analysis, position)
        # ... orchestrates across contexts
```

## 10. Shared Kernel (Bounded Context Integration)

**Shared Kernel**: Minimal agreed-upon types shared between contexts.

Location: `src/domain/shared/`

```python
# src/domain/shared/__init__.py
from .types import UUID, Symbol, Timestamp, Currency

# src/domain/shared/types.py
from uuid import UUID
from enum import Enum

class Symbol(str): ...
class Currency(str): ...
```

**Rules**:
- Shared kernel must be stable and backward compatible
- Changes to shared kernel require multi-context review
- Prefer duplication over premature sharing

## 11. Package Dependency Summary Table

| Layer | Can Import | Must Not Import | Notes |
|-------|-----------|-----------------|-------|
| Domain | Stdlib, typing, __future__ | Application, Infrastructure, Presentation | Pure Python, no framework deps |
| Application | Domain (interfaces + entities), Stdlib | Infrastructure, Presentation | Orchestration only |
| Infrastructure | Domain, Application, Stdlib | Presentation | Implements interfaces |
| Presentation | Application, Stdlib | Infrastructure | Thin adapter, DI only |
| Tests | All | N/A | Test code is exempt |

## 12. Violation Recovery Procedure

When a dependency violation is detected:

1. **Identify**: Use detection script to find violation
2. **Assess**: Determine if violation reflects legitimate architecture
3. **Refactor**:
   - Option A: Move code to appropriate layer
   - Option B: Extract interface to domain, implement in outer layer
   - Option C: Introduce event-driven communication
4. **Document**: Update this document if edge case is accepted
5. **Test**: Run architecture test suite

**Emergency Override**: None allowed. Any approved override requires CTO review and documentation.
