# Layer Architecture

## 1. Clean Architecture Enforcement

QuantX AI implements **Clean Architecture** with strict dependency rules. Dependencies flow **inward only** - outer layers depend on inner layers, never the reverse.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Infrastructure Layer                      │
│  (Quick to change: frameworks, databases, external APIs)        │
│  - Database ORM adapters (SQLAlchemy)                           │
│  - HTTP clients (CCXT, AI APIs)                                 │
│  - File system adapters                                         │
│  - Message queue clients                                        │
│  - Cache implementations                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  (Medium change: use cases, orchestration, workflows)           │
│  - Use case implementations                                     │
│  - Service orchestration                                        │
│  - Transaction management (Unit of Work)                        │
│  - Event publishing                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                         Domain Layer                             │
│  (NEVER changes: core business logic)                           │
│  - Entities (business objects)                                  │
│  - Value Objects (immutable concepts)                           │
│  - Aggregates (consistency boundaries)                          │
│  - Domain Services (complex business rules)                     │
│  - Domain Events (business occurrences)                         │
│  - Repository interfaces (ports)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↑ implemented by
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                           │
│  (Changeable: user interfaces, protocols)                       │
│  - REST API controllers                                         │
│  - Telegram handlers                                            │
│  - WebSocket connections                                        │
│  - DTOs/Request-Response models                                 │
│  - Authentication/Authorization handlers                        │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Layers in Detail

### 2.1 Domain Layer (Core)

**Location**: `src/domain/`

**Absolute Authority**:
- Defines business entities and rules
- Contains NO framework dependencies
- No imports from application, infrastructure, or presentation layers

**Components**:

#### 2.1.1 Entities
```python
# Example concepts (no actual code)
- Trade(Entity)
- Position(Entity)
- Portfolio(Aggregate Root)
- Strategy(Entity)
- Order(Entity)
```

**Characteristics**:
- Have unique identity
- Encapsulate business invariants
- Mutable state with validation
- Contain business behavior (methods)

#### 2.1.2 Value Objects
```python
# Example concepts
- Price(immutable)
- Quantity(immutable)
- Symbol(value object)
- Timestamp(value object)
- Currency(value object)
```

**Characteristics**:
- No identity, equality by value
- Immutable
- Self-validating
- Represent descriptive aspects of domain

#### 2.1.3 Aggregates
```python
# Example concepts
- Portfolio Aggregate
  - Position (entities)
  - Balance (entities)
  - Transaction (entities)

- Order Aggregate
  - OrderLine (entities)
  - Fee (value objects)
```

**Characteristics**:
- Cluster of entities treated as single unit
- Aggregate Root = entry point for modifications
- Enforce invariants across entire aggregate

#### 2.1.4 Domain Services
```python
# Example concepts
- RiskCalculationService
- PortfolioRebalancingService
- OrderMatchingService
- MarketAnalysisService
```

**Characteristics**:
- Complex operations that don't belong to single entity
- Pure business logic, no infrastructure
- Injected as dependencies

#### 2.1.5 Repository Interfaces (Ports)
```python
# Example concepts
class OrderRepository(ABC):
    async def save(self, order: Order) -> None: ...
    async def find_by_id(self, id: UUID) -> Order | None: ...
    async def find_pending_by_symbol(self, symbol: Symbol) -> list[Order]: ...

class MarketDataRepository(ABC):
    async def save_candles(self, candles: list[Candle]) -> None: ...
    async def get_candles(self, symbol: Symbol, timeframe: Timeframe, ...) -> AsyncIterator[Candle]: ...
```

**Characteristics**:
- Define contracts only (no implementation)
- Use Python abstract base classes
- Imported by application layer
- Implemented by infrastructure layer

#### 2.1.6 Domain Events
```python
# Example concepts
- OrderPlaced(DomainEvent)
- OrderExecuted(DomainEvent)
- PositionClosed(DomainEvent)
- RiskThresholdBreached(DomainEvent)
- SignalGenerated(DomainEvent)
```

**Characteristics**:
- Represent something that happened
- Immutable
- Named in past tense
- Used for loose coupling between components

### 2.2 Application Layer

**Location**: `src/application/`

**Responsibility**: Orchestrate domain objects to complete use cases.

**Components**:

#### 2.2.1 Use Cases / Command Handlers
```python
# Example concepts
- PlaceOrderUseCase
- CancelOrderUseCase
- GetPortfolioSummaryUseCase
- GenerateTradingSignalUseCase
- ExecuteStrategyUseCase
```

**Pattern**: Command Query Responsibility Segregation (CQRS)
- **Commands**: Write operations (PlaceOrder, CancelOrder)
- **Queries**: Read operations (GetPortfolio, GetTradeHistory)

**Implementation Pattern**:
```python
class PlaceOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,  # Domain interface
        portfolio_repo: PortfolioRepository,
        event_bus: EventBus,
        unit_of_work: UnitOfWork,
    ):
        ...

    async def execute(self, command: PlaceOrderCommand) -> OrderId:
        async with self.unit_of_work:
            portfolio = await self.portfolio_repo.get_active()
            order = portfolio.place_order(...)  # Domain logic
            await self.order_repo.save(order)
            await self.event_bus.publish(OrderPlaced(order.id))
            return order.id
```

#### 2.2.2 Service Orchestrators
```python
# Example concepts
- TradingOrchestrator
- MarketDataPipeline
- StrategyExecutor
- RiskMonitor
```

**Responsibilities**:
- Coordinate multiple use cases
- Handle cross-cutting concerns
- Manage workflows spanning multiple aggregates

#### 2.2.3 Event Handlers
```python
# Example concepts
- OnOrderPlacedHandler
- OnRiskThresholdBreachedHandler
- OnSignalGeneratedHandler
```

**Responsibilities**:
- React to domain events
- Trigger side effects (notifications, logging)
- Maintain eventual consistency

#### 2.2.4 Unit of Work
```python
class UnitOfWork:
    async def __aenter__(self):
        await self.begin()
        return self

    async def __aexit__(self, *args):
        await self.commit()

    async def begin(self): ...
    async def commit(self): ...
    async def rollback(self): ...
```

**Responsibilities**:
- Transaction boundary management
- Atomicity guarantees
- Repository collection management

### 2.3 Infrastructure Layer

**Location**: `src/infrastructure/`

**Responsibility**: Implement interfaces defined in domain layer.

**Components**:

#### 2.3.1 Repository Implementations
```python
class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    async def save(self, order: Order) -> None:
        # Map domain Order to ORM model
        # Persist to PostgreSQL
        ...

    async def find_by_id(self, id: UUID) -> Order | None:
        # Query database
        # Map ORM model to domain Order
        ...
```

#### 2.3.2 External Service Adapters
```python
class CCXTExchangeAdapter:
    async def fetch_ticker(self, symbol: str) -> MarketTicker: ...
    async def fetch_order_book(self, symbol: str) -> OrderBook: ...
    async def create_order(self, order: Order) -> ExchangeOrder: ...
    async def cancel_order(self, order_id: str) -> None: ...

class GeminiAIAdapter:
    async def analyze_market(self, prompt: str) -> AIAnalysis: ...
    async def assess_risk(self, context: RiskContext) -> RiskAssessment: ...
```

#### 2.3.3 Caching Implementations
```python
class RedisMarketDataCache:
    async def get_candles(self, key: str) -> list[Candle] | None: ...
    async def set_candles(self, key: str, candles: list[Candle], ttl: int) -> None: ...
```

#### 2.3.4 Message Queue Clients
```python
class RedisPubSubPublisher:
    async def publish(self, channel: str, message: EventMessage) -> None: ...
    async def subscribe(self, channel: str) -> AsyncIterator[EventMessage]: ...
```

### 2.4 Presentation Layer

**Location**: `src/presentation/`

**Responsibility**: Handle user interactions, translate between external formats and internal models.

**Components**:

#### 2.4.1 REST Controllers
```python
class TradingController:
    def __init__(self, place_order_use_case: PlaceOrderUseCase):
        self.place_order_use_case = place_order_use_case

    @router.post("/orders")
    async def place_order(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        command = PlaceOrderCommand(...)  # Map DTO to command
        order_id = await self.place_order_use_case.execute(command)
        return PlaceOrderResponse(order_id=order_id)
```

#### 2.4.2 Telegram Handlers
```python
class TelegramTradingHandler:
    def __init__(self, place_order_use_case: PlaceOrderUseCase):
        self.place_order_use_case = place_order_use_case

    @router.message(Command("buy"))
    async def handle_buy_command(self, message: Message) -> None:
        command = PlaceOrderCommand(...)  # Parse Telegram message
        await self.place_order_use_case.execute(command)
        await message.reply("Order placed successfully")
```

#### 2.4.3 WebSocket Connections
```python
class MarketDataWebSocket:
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service

    async def stream_candles(self, websocket: WebSocket, symbol: str):
        async for candle in self.market_data_service.subscribe(symbol):
            await websocket.send_json(candle.to_dict())
```

#### 2.4.4 Request/Response DTOs
```python
class PlaceOrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal | None = None
    order_type: OrderType

class PlaceOrderResponse(BaseModel):
    order_id: UUID
    status: OrderStatus
    message: str
```

**Characteristics**:
- Pydantic models for validation
- Defined in presentation layer, never leak to domain/application
- Map to commands/queries at boundary

## 3. Cross-Cutting Concerns

### 3.1 Dependency Injection Container
**Location**: `src/infrastructure/di/`

Frameworks and implementations provisioned here:
- Database session factories
- Repository implementations
- External API clients
- Service implementations

**Resolution Strategy**:
- Constructor injection (preferred)
- Interface-based resolution
- Lifetime: Scoped to request (web) or event (background tasks)

### 3.2 Transaction Management
- Unit of Work pattern in application layer
- SQLAlchemy session scoped to use case
- Automatic rollback on exceptions
- Explicit commit at success boundary

### 3.3 Event Bus
**Location**: `src/infrastructure/events/`

In-process event bus for:
- Domain event propagation
- Decoupled side effects
- Saga orchestration (complex workflows)

**Implementation**: Redis Pub/Sub for multi-process scenarios

### 3.4 Caching Strategy
```
L1: In-process LRU (request-scoped)
  ↓ miss
L2: Redis (shared, TTL-based)
  ↓ miss
L3: Database / External API
```

**Cache Invalidation**:
- Time-based expiration (primary)
- Event-based invalidation (trade execution)
- Manual invalidation endpoints

## 4. Layer Communication Rules

### Allowed Dependencies

| Layer Can Depend On | Domain | Application | Infrastructure | Presentation |
|--------------------|--------|-------------|----------------|--------------|
| **Domain**         | ❌     | ❌          | ❌             | ❌           |
| **Application**    | ✅     | ❌          | ❌             | ❌           |
| **Infrastructure** | ✅     | ✅          | ❌             | ❌           |
| **Presentation**   | ✅     | ✅          | ✅             | ❌           |

### Cross-Cutting Rules
1. **Domain is pure**: No framework imports, no async def (use `__future__` annotations)
2. **Application defines interfaces**: Infrastructure implements
3. **Presentation handles I/O**: All I/O at boundaries, pure functions within
4. **Dependency Inversion**: Always depend on abstractions, never concretions

## 5. Common Architecture Anti-Patterns to Avoid

### ❌ Anemic Domain Model
- Domain entities with only getters/setters
- Business logic in services instead of entities

### ❌ Fat Services
- Services doing too much
- Violation of Single Responsibility Principle

### ❌ God Objects
- Classes doing everything
- Lack of separation of concerns

### ❌ Leaky Abstractions
- Exposing ORM models to API layer
- Framework types in domain layer

### ❌ Circular Dependencies
- Must be prevented by strict layer rules
- Detected at CI pipeline

### ❌ Smart UI
- Business logic in controllers/handlers
- Frontend making business decisions
