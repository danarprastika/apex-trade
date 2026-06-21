# Project Conventions

## 1. Development Philosophy

### 1.1 DDD Ubiquitous Language
The codebase MUST use vocabulary consistent with the domain. NO translation between business and technical terms.

```python
# Ubiquitous language applied:
# BAD: user, trade, account, symbol
# GOOD: trader (user), position (open trade), portfolio (account), ticker (symbol)

class Portfolio:  # NOT Account
    """Trader's portfolio tracking open positions and balances."""

    def close_position(self, position: Position) -> Trade:
        """Close an open position, realizing P&L."""
        ...

# Bad language example to avoid
class Account:  # WRONG - inconsistent naming
    def get_balance(self): ...
```

### 1.2 Domain-Driven Design Enforcement
```python
# Entities contain business behavior, not just data
class Position:
    def close(self, exit_price: Price) -> Trade:
        """Close position and return resulting trade record."""
        # Business logic resides IN the entity
        pnl = self.unrealized_pnl(exit_price)
        ...
        return Trade(position=self, exit_price=exit_price, pnl=pnl)
```

## 2. Anti-Patterns to Avoid

### 2.1 Anemic Domain Model ❌
```python
# BAD: Entities are just data containers
class Trade:
    price: Decimal  # Just data
    quantity: Decimal  # Just data

# External service does business logic
def calculate_trade_value(trade):
    return trade.price * trade.quantity
```

```python
# GOOD: Rich domain model
class Trade:
    def __init__(self, price: Price, quantity: Quantity):
        self._price = price
        self._quantity = quantity

    def value(self) -> Price:
        """Calculate total value of the trade."""
        return self._price * self._quantity
```

### 2.2 Service-Only Objects ❌
```python
# BAD: Everything in service, domain ignores responsibility
class OrderService:
    def place_order(self, symbol, side, qty):
        # 200 lines of business logic here
        ...

class Order:
    pass  # Empty entity
```

```python
# GOOD: Split behavior appropriately
class Order:
    def fill(self, execution: Execution) -> None:
        """Mark order as filled with execution details."""
        self._status = OrderStatus.FILLED
        self._filled_quantity = self._quantity

class OrderService:
    def place_order(self, command: PlaceOrderCommand) -> OrderId:
        """Orchestrate order placement."""
        # Validation only
        # Delegate to Order entity
        order = Portfolio.create_order(...)
        # Persistence via repository
        order_id = await self._order_repo.save(order)
        return order_id
```

### 2.3 Magic Numbers and Strings ❌
```python
# BAD
if order.price > 999999:
    raise ValueError("Invalid price")

# GOOD
MAX_ORDER_PRICE = Price(Decimal("999999"))
MIN_ORDER_QUANTITY = Quantity(Decimal("0.00000001"))

if order.price > MAX_ORDER_PRICE:
    raise ValueError(f"Price exceeds maximum: {MAX_ORDER_PRICE}")
```

### 2.4 God Object ❌
```python
# BAD: Single class doing everything
class TradingSystem:
    def place_order(self): ...
    def cancel_order(self): ...
    def get_portfolio(self): ...
    def analyze_market(self): ...
    def send_notification(self): ...
```

```python
# GOOD: Focused, single-responsibility classes
class OrderService: ...
class PortfolioService: ...
class MarketAnalysisService: ...
class NotificationService: ...
```

### 2.5 Leaky Abstractions ❌
```python
# BAD: ORM model leaks to API layer
@router.get("/orders/{order_id}")
async def get_order(order_id: UUID) -> SqlAlchemyOrder:  # WRONG
    return await db.query(SqlAlchemyOrder).get(order_id)
```

```python
# GOOD: API returns domain DTO
@router.get("/orders/{order_id}")
async def get_order(order_id: UUID) -> OrderResponse:
    order = await place_order_use_case.execute(command)
    return OrderResponse.from_entity(order)
```

## 3. Success Criteria

### 3.1 Primary Success Metrics
- **Zero-layer violations**: CI enforces zero cross-layer imports
- **100% type coverage**: All functions annotated
- **80% test coverage**: Business critical paths covered
- **Zero blocking in async**: No sync I/O in async code paths
<br>
### 3.2 Secondary Success Metrics
- **Zero god objects**: No class > 500 lines
- **P95 latency < 500ms**: API responses
- **99.9% uptime**: Production target
- **Zero domain logic in presentation**: Separation of concerns
<br>
## 4. Severity Decorators

### 4.1 Error Severity Levels
Decorators indicate how critical errors are and what action should be taken:

```python
from dataclasses import dataclass

@dataclass
class TradingErrorSeverity:
    CRITICAL = "critical"   # System halt, manual intervention required
    HIGH = "high"          # Major feature failure, auto-recovery
    MEDIUM = "medium"      # Partial degradation, continued operation
    LOW = "low"            # Informational, no user impact
```

### 4.2 Usage in Domain Errors
```python
class OrderExecutionError(TradingError):
    """Error during order execution."""
    severity = ErrorSeverity.HIGH
    retryable = True
    user_message = "Order failed to execute. Please try again."
```

### 4.3 Severity Classification Guide

| Severity | Action Required | Example |
|----------|-----------------|---------|
| Critical | Halt, investigate, manual fix | DB corruption, data loss |
| High | Auto-retry with backoff | Exchange API unavailable |
| Medium | Log and continue | Partial data load failure |
| Low | Log only | Non-critical cache miss |

## 5. Common Patterns and Best Practices

### 5.1 Exception Chaining
Always preserve error context using `raise ... from ...`

```python
try:
    order = await exchange.create_order(...)
except ExchangeAPIError as e:
    raise OrderExecutionError(f"Failed to place order: {order.id}") from e
```

### 5.2 Validation at Boundaries
Validate all external input immediately at presentation layer

```python
# presentation/api/v1/trading/schemas.py
class PlaceOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: Annotated[str, Field(min_length=3, max_length=20)]
    quantity: Annotated[Decimal, Field(gt=0)]
```

### 5.3 Async Context Managers for Transactions

```python
async with self._unit_of_work:
    order = await self._order_repo.save(order)
    position = await self._position_repo.save(position)
    await self._event_bus.publish(OrderPlaced(order=order))
# Automatic commit on success, rollback on exception
```

### 5.4 Event-Driven Architecture (In-Process)

```python
# Publish
await self.event_bus.publish(OrderPlaced(order=order))

# Subscribe (in application event handler)
@event_handler(OrderPlaced)
async def on_order_placed(event: OrderPlaced):
    await notification_service.notify_order_placed(event.order)
```

### 5.5 Repository Pattern (Unit of Work)

```python
class UnitOfWork:
    """Manage transaction boundary and repository lifecycle."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(self, *args) -> None:
        try:
            await self.commit()
        except Exception:
            await self.rollback()
            raise
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

### 5.6 CQRS Pattern Summary

```
Commands (Write):
  PlaceOrderCommand → PlaceOrderUseCase → OrderAggregate → OrderRepository.save()

Queries (Read):
  GetPortfolioQuery → GetPortfolioQueryHandler → PortfolioRepository.get_active() → PortfolioDto
```

### 5.7 Fail-Fast Validation
Validate early, fail fast

```python
# In use case
def validate(self, command: PlaceOrderCommand) -> None:
    if command.quantity <= ZERO:
        raise ValidationError("Quantity must be positive")
    if not is_valid_symbol(command.symbol):
        raise ValidationError(f"Invalid symbol: {command.symbol}")
    # Only proceed after validation passes
    order = self._portfolio.place_order(command)
```

### 5.8 Immutability Where Possible
Use frozen dataclasses for value objects

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Price:
    value: Decimal

    def __post_init__(self) -> None:
        if self.value < ZERO:
            raise ValueError("Price cannot be negative")
```

### 5.9 Fluent Builder for Complex Objects
```python
order = OrderBuilder() \
    .with_symbol("BTC/USDT") \
    .with_side(OrderSide.BUY) \
    .with_quantity(Decimal("0.1")) \
    .as_limit_order(limit_price=Price(30000)) \
    .build()
```

## 6. Code Review Checklist

- [ ] No cross-layer imports (except via domain interfaces)
<br>
- [ ] All functions have type hints
<br>
- [ ] Domain logic resides in domain layer
<br>
- [ ] Presentation layer only translates (doesn't decide)
<br>
- [ ] No blocking calls in async code
<br>
- [ ] Exceptions chained with `from ...`
<br>
- [ ] Docstrings present for public methods
<br>
- [ ] Pydantic models have validation rules
<br>
- [ ] Testability: Can I mock this easily?
<br>
- [ ] No leaked ORM models to API layer
<br>
- [ ] Single responsibility met for classes/functions
<br>
- [ ] Meaningful variable/function names (no cryptic abbreviations)

## 7. Version Control Conventions

### 7.1 Git Commit Message Format
Follow the Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`
**Scopes**: `domain`, `application`, `infrastructure`, `presentation`, `trading`, `market_data`, `portfolio`

**Examples**:
```
feat(trading): add support for stop-loss order type
fix(portfolio): fix unrealized PnL calculation for short positions
refactor(domain): extract price validation into Price value object
docs(api): document new /portfolio/summary endpoint
chore(deps): upgrade FastAPI to 0.111.0
```

### 7.2 Branch Naming
```
feature/<description>
bugfix/<description>
hotfix/<description>
refactor/<description>
chore/<description>
```

## 8. Database Migration Naming

Alembic migrations follow pattern:

```
YYYYMMDD_HHMMSS_description.py
```

**Examples**:
```
20250115_143022_add_orders_table.py
20250120_091015_add_strategies_table.py
20250122_165430_add_index_to_orders_symbol.py
```

**Revision message** (in migration file):
```python
"""Add orders table.

Revision ID: abc123
Revises: def456
Create Date: 2025-01-15 14:30:22
"""

# revision identifiers
revision = "abc123"
down_revision = "def456"
branch_labels = None
depends_on = None
```

## 9. LLM/AI Integration Best Practices

### 9.1 Prompt Management
Store prompts as versioned templates

```python
# config/prompts/market_analysis.txt
SYSTEM_PROMPT = """You are QuantX AI, a trading assistant.

Analyze the following market data and provide:
1. Direction prediction (BUY/SELL/HOLD)
2. Confidence score (0.0-1.0)
3. Technical reasoning
4. Risk factors

Response must be in strict JSON format:
{{
  "direction": "...",
  "confidence": ...,
  "reasoning": "...",
  "risk_factors": [...]
}}
"""

USER_PROMPT_TEMPLATE = """Symbol: {symbol}
Timeframe: {timeframe}
Recent candles: {candles}
Current indicators: {indicators}
"""
```

### 9.2 Response Parsing
Always validate AI responses against strict schema

```python
class AIAnalysisResponse(BaseModel):
    direction: Literal["BUY", "SELL", "HOLD"]
    confidence: confloat(ge=0, le=1)
    reasoning: str
    risk_factors: list[str]
```

### 9.3 Failover Strategy
```python
class AIRouter:
    async def analyze(self, prompt: str) -> AIAnalysisResponse:
        try:
            return await self._gemini.analyze(prompt)
        except Exception as e:
            logger.warning("Gemini failed, falling back to OpenRouter", exc_info=e)
            return await self._openrouter.analyze(prompt)
```

### 9.4 Caching AI Responses
For cost optimization, cache AI analysis results

```python
# Redis cache with 5-minute TTL for market analysis
cached_analysis = await self._cache.get(f"analysis:{symbol}:{timeframe}")
if cached_analysis:
    return AIAnalysisResponse.parse_raw(cached_analysis)

analysis = await self._ai_router.analyze(prompt)
await self._cache.set(f"analysis:{symbol}:{timeframe}", analysis.json(), ttl=300)
```

## 10. Design Decision Documentation

Every major architectural decision MUST be documented:

```markdown
## Decision: Why SQLAlchemy over raw SQL?

### Context
Need ORM with async support, migration tooling, and type safety.

### Options
1. SQLAlchemy 2.x async
2. Tortoise ORM
3. Raw SQL with asyncpg

### Decision: SQLAlchemy 2.x
**Rationale**:
- Industry standard for Python async ORM
- Alembic native migration support
- Excellent type stubs and Pydantic integration
- Large community and documentation

### Trade-offs Accepted
- Slightly more verbose than Tortoise
- Steeper learning curve

### Consequences
- Team must learn SQLAlchemy patterns
- Future migrations may need alembic expertise
```

## 11. Code Review Checklist

Every PR must include:
- [ ] Architecture diagram for new component
- [ ] Updated module dependency graph
- [ ] Migration plan for database changes
- [ ] Performance impact assessment
- [ ] Security review checklist
- [ ] Documentation updates
- [ ] Test plan review
- [ ] Rollback procedure
