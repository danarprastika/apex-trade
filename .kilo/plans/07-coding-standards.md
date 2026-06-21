# Coding Standards

## 1. Python Code Style

### 1.1 PEP 8 Compliance
All Python code MUST adhere to PEP 8 with these project-specific additions:

- **Line Length**: 100 characters (strict)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Sorted using `ruff` or `isort`
- **String Quotes**: Double quotes preferred, single quotes for internal strings

### 1.2 Type Hints (MANDATORY)
Every function and method MUST have type annotations. No exceptions.

```python
# GOOD
async def calculate_pnl(
    self,
    position: Position,
    current_price: Price,
) -> PnL:
    ...

# BAD
async def calculate_pnl(self, position, current_price):
    ...
```

**Special rules**:
- Use `from __future__ import annotations` to enable forward references
- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Use `list[X]` instead of `List[X]` from typing
- Use `X | Y` union syntax instead of `Union[X, Y]`
- `TYPE_CHECKING` guard for imports only used in annotations

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities import Order

async def find_order(self, id: UUID) -> Order | None:
    ...
```

### 1.3 Async/Await Patterns
All I/O operations MUST be async in application and domain layers.

```python
# GOOD - Async repository
class OrderRepository(ABC):
    @abstractmethod
    async def save(self, order: Order) -> None:
        ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Order | None:
        ...

# GOOD - Awaiting async calls
async def execute(self, command: PlaceOrderCommand) -> OrderId:
    async with self.unit_of_work:
        order = self._portfolio.place_order(...)
        await self._order_repo.save(order)
        return order.id

# BAD - Blocking in async context
async def execute(self, command: PlaceOrderCommand) -> OrderId:
    result = some_blocking_function()  # BLOCKS EVENT LOOP
    ...
```

**Rule**: In application/domain layers, use `asyncio.to_thread()` if calling sync code.

```python
result = await asyncio.to_thread(sync_function, arg1, arg2)
```

### 1.4 Error Handling in Async Context
All exceptions MUST be handled explicitly.

```python
# GOOD - Explicit exception handling
async def execute(self, command: PlaceOrderCommand) -> OrderId:
    try:
        async with self.unit_of_work:
            ...
            await self._event_bus.publish(OrderCreated(order=order))
    except InsufficientBalanceError:
        raise OrderExecutionError("Insufficient balance") from None
    except ExchangeAPIError as e:
        raise OrderExecutionError(f"Exchange error: {e}") from e
```

### 1.5 Immutability and Mutability

**Domain Value Objects**: Always immutable
```python
@dataclass(frozen=True)
class Price:
    value: Decimal

    def __post_init__(self) -> None:
        if self.value < ZERO:
            raise ValueError("Price must be non-negative")
```

**Domain Entities**: Mutable by design (identity-based)
```python
class Order:
    def __init__(self, id: UUID, symbol: Symbol):
        self._id = id
        self._symbol = symbol
        self._status = OrderStatus.PENDING

    # Use methods to modify state
    def fill(self, quantity: Quantity, price: Price) -> ExecutionReport:
        self._status = OrderStatus.FILLED
        ...
```

**DTOs (Pydantic)**: Immutable preferred
```python
class OrderDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    symbol: str
    side: OrderSide
    quantity: Decimal
```

## 2. Pydantic Model Standards

### 2.1 Model Configuration
All Pydantic models MUST use type-safe configuration:

```python
from pydantic import BaseModel, ConfigDict, Field

class PlaceOrderRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",  # Strict validation
    )

    symbol: str = Field(..., min_length=3, max_length=20)
    quantity: Decimal = Field(..., gt=0, decimal_places=8)
    side: OrderSide
```

### 2.2 Validation Rules
- Use Pydantic validators for complex validation
- Raise domain-specific validation errors
- Never silent-validate (fail fast)

```python
from pydantic import field_validator

class OrderCreateRequest(BaseModel):
    price: Decimal | None = None

    @field_validator("price")
    @classmethod
    def validate_price_for_limit_order(cls, v: Decimal | None, info: FieldValidationInfo) -> Decimal | None:
        if info.data.get("order_type") == OrderType.LIMIT and v is None:
            raise ValueError("Limit order requires price")
        return v
```

## 3. Docstring Standards

### 3.1 Google Style Docstrings

```python
def calculate_pnl(
    self,
    position: Position,
    current_price: Price,
) -> PnL:
    """Calculate unrealized profit/loss for a position.

    Computes the difference between current market value and
    average entry price, accounting for position side (long/short).

    Args:
        position: The position to evaluate
        current_price: Current market price of the asset

    Returns:
        PnL value (positive for profit, negative for loss)

    Raises:
        ValueError: If position quantity <= 0
        InvalidPriceError: If current_price is not positive

    Example:
        >>> position = Position(symbol="BTC", side=BUY, quantity=1, avg_price=30000)
        >>> pnl = service.calculate_pnl(position, Price(35000))
        >>> assert pnl.value > 0  # Profit
    """
    if position.quantity <= ZERO:
        raise ValueError("Position quantity must be positive")
    if current_price <= ZERO:
        raise InvalidPriceError("Price must be positive")
    ...
```

### 3.2 Module Docstrings
Every module MUST have a module-level docstring:

```python
"""Order management module.

This module contains the Order aggregate and related value objects
for managing trade orders within the QuantX trading system.

The Order aggregate enforces business rules including:
- Positive quantity validation
- Valid status transitions
- Consistent price validation per order type
"""

from __future__ import annotations
```

### 3.3 Package Docstrings
Each package (directory) with `__init__.py`:

```python
"""Domain layer - core business logic.

This package contains the pure domain model of the QuantX trading
platform. It has ZERO dependencies on frameworks or infrastructure.
"""

from .entities import Trade, Order, Position, Portfolio
from .value_objects import Price, Quantity, Symbol
from .repositories import OrderRepository, MarketDataRepository
```

## 4. SQLAlchemy Model Standards

### 4.1 Model Definition

```python
from sqlalchemy import (
    Column, String, Numeric, DateTime, Enum, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime
from decimal import Decimal

Base = declarative_base()

class SqlAlchemyOrder(Base):
    """SQLAlchemy ORM model for Order aggregate."""
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_status", "status"),
        Index("idx_orders_symbol", "symbol"),
        Index("idx_orders_portfolio", "portfolio_id"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)

    # Fields (snake_case for DB consistency)
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    filled_quantity = Column(Numeric(precision=18, scale=8), nullable=False, default=0)
    limit_price = Column(Numeric(precision=18, scale=8), nullable=True)
    stop_price = Column(Numeric(precision=18, scale=8), nullable=True)
    time_in_force = Column(Enum(TimeInForce), nullable=False, default=TimeInForce.GTC)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    exchange_order_id = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
```

### 4.2 Mapper Pattern
Separate domain entity from ORM model:

```python
# Domain ↔ ORM mapping (in repository implementation)
class SqlAlchemyOrderRepository(OrderRepository):
    def _to_entity(self, model: SqlAlchemyOrder) -> Order:
        return Order(
            id=model.id,
            symbol=model.symbol,
            side=model.side,
            order_type=model.order_type,
            quantity=model.quantity,
            ...
        )

    def _to_model(self, entity: Order) -> SqlAlchemyOrder:
        return SqlAlchemyOrder(
            id=entity.id,
            symbol=entity.symbol,
            side=entity.side,
            ...
        )
```

## 5. Logging Standards

### 5.1 Structured Logging
Use Python `logging` module with JSON formatter.

```python
import logging
import json
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# GOOD - Structured logging
logger.info(
    "Order placed",
    extra={
        "order_id": str(order.id),
        "symbol": order.symbol,
        "side": order.side,
        "quantity": float(order.quantity),
        "user_id": str(user_id),
    },
)

# BAD - String formatting
logger.info(f"Order placed: {order.id} for {order.symbol}")
```

### 5.2 Logger Naming

```python
# Use module path as logger name
import logging
logger = logging.getLogger(__name__)  # Results in: src.application.use_cases.place_order

# For specific components
order_logger = logging.getLogger("trading.orders")
risk_logger = logging.getLogger("risk.monitoring")
```

### 5.3 Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed diagnostic info | `logger.debug("Processing candle batch", ...)` |
| INFO | General informational | `logger.info("Order placed", ...)` |
| WARNING | Recoverable issues | `logger.warning("Rate limit approaching for exchange", ...)` |
| ERROR | Failures requiring attention | `logger.error("Order execution failed", exc_info=True)` |
| CRITICAL | System failure | `logger.critical("Database connection lost", ...)` |

### 5.4 Exceptions and Error Context
Always log exceptions with context:

```python
try:
    order = await self._execute_order(command)
except ExchangeAPIError as e:
    logger.error(
        "Order execution failed",
        extra={
            "order_id": command.id,
            "symbol": command.symbol,
            "error": str(e),
        },
        exc_info=True,  # Include traceback
    )
    raise OrderExecutionError("Order failed") from e
```

## 6. Pytest Testing Standards

### 6.1 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── domain/
│   │   └── test_entities.py
│   ├── application/
│   │   └── test_trading_service.py
│   └── infrastructure/
│       └── test_repository.py
├── integration/
│   ├── test_api_trading.py
│   └── test_database.py
└── e2e/
    └── test_workflows.py
```

### 6.2 Fixture Naming

```python
import pytest
from src.domain.entities import Order
from src.domain.value_objects import Price

@pytest.fixture
def sample_order() -> Order:
    """Create a sample order for testing."""
    return Order(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.1"),
        limit_price=Price(Decimal("30000")),
    )

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for testing."""
    async with async_session() as session:
        yield session
        await session.rollback()
```

### 6.3 Test Function Naming

```python
def test_order_creation_valid_input() -> None:
    """Test creating an order with valid parameters."""
    ...

def test_order_creation_negative_quantity_raises_error() -> None:
    """Test that negative quantity raises ValueError."""
    with pytest.raises(ValueError, match="Quantity must be positive"):
        Order(quantity=Decimal("-1"))

@pytest.mark.asyncio
async def test_order_repository_save_and_fetch() -> None:
    """Test persisting and retrieving order from database."""
    ...
```

### 6.4 Parametrize for Similar Tests

```python
@pytest.mark.parametrize(
    "order_type,required_field,valid_value",
    [
        (OrderType.LIMIT, "limit_price", Decimal("30000")),
        (OrderType.STOP_LIMIT, "stop_price", Decimal("28000")),
    ],
)
def test_limit_orders_require_price_field(
    self, order_type: OrderType, required_field: str, valid_value: Decimal
) -> None:
    """Test that limit-based orders require their price fields."""
    ...
```

### 6.5 Async Test Patterns

```python
@pytest.mark.asyncio
async def test_place_order_succeeds(order_repo: OrderRepository) -> None:
    """Test successful order placement."""
    use_case = PlaceOrderUseCase(order_repo=order_repo, ...)
    result = await use_case.execute(command)
    assert result is not None
```

### 6.6 Mocking Strategy
Use `unittest.mock.AsyncMock` for async, `unittest.mock.Mock` for sync.

```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.fixture
def mock_order_repo() -> MagicMock:
    return MagicMock(spec=OrderRepository)

@pytest.mark.asyncio
async def test_place_order_uses_repository(mock_order_repo: MagicMock) -> None:
    """Test that use case calls repository save."""
    mock_order_repo.save = AsyncMock()
    use_case = PlaceOrderUseCase(order_repo=mock_order_repo, ...)
    await use_case.execute(command)
    mock_order_repo.save.assert_called_once()
```

## 7. FastAPI Standards

### 7.1 Endpoint Organization

```python
# presentation/api/v1/trading/router.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/trading", tags=["trading"])

@router.post("/orders", response_model=OrderResponse)
async def place_order(
    request: PlaceOrderRequest,
    use_case: PlaceOrderUseCase = Depends(get_place_order_use_case),
) -> OrderResponse:
    """Place a new trading order."""
    command = PlaceOrderCommand(...)
    order_id = await use_case.execute(command)
    return OrderResponse(order_id=order_id, status="open")
```

### 7.2 Response Models (Pydantic)
Use Pydantic models for all responses:

```python
class OrderResponse(BaseModel):
    order_id: UUID
    symbol: str
    side: OrderSide
    quantity: Decimal
    status: OrderStatus
    created_at: datetime
```

### 7.3 Exception Handling Middleware

```python
# presentation/api/middleware.py
class ExceptionHandlerMiddleware:
    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except DomainError as e:
            return JSONResponse(
                status_code=400,
                content={"error": "domain_error", "message": str(e)},
            )
        except ExchangeAPIError as e:
            return JSONResponse(
                status_code=502,
                content={"error": "exchange_error", "message": str(e)},
            )
```

## 8. aiogram Handler Standards

### 8.1 Handler Organization

```python
# presentation/telegram/handlers.py
from aiogram import Router, types

router = Router(name="trading")

@router.message(Command("buy"))
async def handle_buy(message: types.Message) -> None:
    ...

@router.message(Command("sell"))
async def handle_sell(message: types.Message) -> None:
    ...

@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def handle_confirmation(callback: types.CallbackQuery) -> None:
    ...
```

### 8.2 Middleware for Authentication

```python
# presentation/telegram/middlewares.py
class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = data["event_from_user"].id
        # Verify user is authorized
        if not await self._is_authorized(user_id):
            await event.answer("Unauthorized")
            return
        return await handler(event, data)
```

## 9. Code Complexity Limits

- **Cyclomatic Complexity**: Max 10 per function
- **Function Length**: Max 50 lines
- **Class Length**: Max 300 lines
- **Parameter Count**: Max 5 parameters

```python
# BAD - 6 parameters, single responsibility violated
def create_order(
    symbol, side, quantity, price, type, exchange, portfolio_id, user_id
):
    ...

# GOOD - Command object consolidates parameters
class PlaceOrderCommand:
    symbol: str
    side: OrderSide
    quantity: Quantity
    order_type: OrderType
    limit_price: Price | None
    portfolio_id: UUID
    user_id: UUID

def execute(self, command: PlaceOrderCommand) -> OrderId:
    ...
```

## 10. Linting Configuration (ruff)

```toml
# pyproject.toml [tool.ruff]
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]
ignore = ["E501"]  # (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

## 11. Formatting (Ruff)

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```
