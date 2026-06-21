# Error Handling Standards

## 1. Error Handling Philosophy

All failures in QuantX AI are **explicit, typed, and recoverable where possible**. Silent failures and swallowed exceptions are strictly forbidden. The goal is to always provide actionable information to users and operators.

**Core Principle**: Quick failure, clean recovery, complete clarity on what happened.

## 2. Exception Hierarchy

QuantX AI uses a typed exception hierarchy defined at the domain layer.

```
TradingError (base)
├── DomainError
│   ├── OrderExecutionError
│   │   ├── InsufficientBalanceError
│   │   ├── InvalidOrderParametersError
│   │   └── OrderRejectedError
│   ├── PositionError
│   │   ├── PositionNotFoundError
│   │   ├── PositionAlreadyClosedError
│   │   └── InsufficientPositionError
│   ├── PortfolioError
│   ├── StrategyError
│   │   ├── StrategyNotFoundError
│   │   ├── InvalidStrategyConfigurationError
│   │   └── StrategyExecutionError
│   └── ValidationError
│       ├── InvalidPriceError
│       ├── InvalidQuantityError
│       └── SymbolNotFoundError
│
├── InfrastructureError
│   ├── DatabaseError
│   │   ├── ConnectionError
│   │   ├── IntegrityError
│   │   └── QueryError
│   ├── CacheError
│   ├── ExchangeAPIError
│   │   ├── RateLimitError
│   │   ├── AuthenticationError
│   │   └── NetworkError
│   └── AIProviderError
│       ├── RateLimitError
│       ├── ContentFilterError
│       └── ModelNotFoundError
│
├── TradingSystemError
│   ├── ConfigurationError
│   ├── UnauthorizedError
│   └── ForbiddenError
│
└── ExternalServiceError
    ├── TelegramAPIError
    ├── NotificationError
    └── WebSocketError
```

### 2.1 Base Exception Definition

```python
# domain/exceptions.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(kw_only=True)
class TradingError(Exception):
    """Base exception for all QuantX AI errors."""

    message: str
    code: str | None = None
    details: dict[str, Any] | None = None
    retryable: bool = False
    user_message: str | None = None

    def __str__(self) -> str:
        return self.message


class DomainError(TradingError):
    """Errors in domain logic."""
    retryable = False


class InfrastructureError(TradingError):
    """Errors in infrastructure layer."""
    retryable = True


class TradingSystemError(TradingError):
    """System-level errors."""
    retryable = False
```

### 2.2 Domain Exceptions

```python
class OrderExecutionError(DomainError):
    """Failed to execute order due to domain validation."""

    retryable = False


class InsufficientBalanceError(OrderExecutionError):
    """Not enough balance to execute order."""

    def __init__(self, required: Price, available: Price, currency: str) -> None:
        super().__init__(
            message=f"Insufficient balance: required {required}, available {available} {currency}",
            code="INSUFFICIENT_BALANCE",
            details={"required": str(required), "available": str(available)},
            user_message=f"Insufficient {currency} balance to complete this order",
        )


class InvalidOrderParametersError(DomainError):
    """Order parameters violate business rules."""

    retryable = False
    user_message = "Invalid order parameters provided"


class OrderRejectedError(OrderExecutionError):
    """Order rejected by exchange."""

    def __init__(self, reason: str, exchange: str) -> None:
        super().__init__(
            message=f"Order rejected by {exchange}: {reason}",
            code="ORDER_REJECTED",
            details={"exchange": exchange, "reason": reason},
            user_message=f"Exchange {exchange} rejected the order: {reason}",
        )
```

### 2.3 Infrastructure Exceptions

```python
class DatabaseError(InfrastructureError):
    """Database operation failed."""
    retryable = True


class ConnectionError(DatabaseError):
    """Database connection failed."""


class IntegrityError(DatabaseError):
    """Database integrity constraint violated."""


class QueryError(DatabaseError):
    """Query execution failed."""


class CacheError(InfrastructureError):
    """Cache operation failed."""
    retryable = True


class ExchangeAPIError(InfrastructureError):
    """External exchange API error."""

    def __init__(self, exchange: str, error: str, retryable: bool = False) -> None:
        super().__init__(
            message=f"Exchange API error from {exchange}: {error}",
            code=f"EXCHANGE_{exchange.upper()}_ERROR",
            details={"exchange": exchange, "error": error},
            retryable=retryable,
            user_message=f"Trading service {exchange} is currently unavailable",
        )
```

### 2.4 System Exceptions

```python
class UnauthorizedError(TradingSystemError):
    """User not authenticated."""

    def __init__(self) -> None:
        super().__init__(
            message="Authentication required",
            code="UNAUTHORIZED",
            user_message="Please authenticate to access this resource",
        )


class ForbiddenError(TradingSystemError):
    """User lacks required permissions."""

    def __init__(self, resource: str) -> None:
        super().__init__(
            message=f"Access forbidden to resource: {resource}",
            code="FORBIDDEN",
            details={"resource": resource},
            user_message="You do not have permission to access this resource",
        )
```

## 3. Exception Handling Patterns

### 3.1 Domain Layer

Domain layer contains **pure business logic**. Exceptions are raised for invariant violations.

```python
class Order:
    """Order aggregate."""

    def fill(self, quantity: Quantity, price: Price) -> ExecutionReport:
        """Fill portion of the order."""
        if quantity <= ZERO:
            raise ValidationError(message="Fill quantity must be positive")

        if self._status not in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED):
            raise OrderExecutionError(
                message=f"Cannot fill order in state {self._status}"
            )

        if self._filled_quantity + quantity > self._quantity:
            raise OrderExecutionError(message="Fill quantity exceeds remaining order")

        self._filled_quantity += quantity
        self._status = OrderStatus.FILLED if self._filled_quantity == self._quantity else OrderStatus.PARTIALLY_FILLED

        return ExecutionReport(
            order_id=self._id,
            status=self._status,
            filled_quantity=self._filled_quantity,
            average_price=price,
            timestamp=datetime.now(timezone.utc),
        )
```

### 3.2 Application Layer

Application layer **catches** domain exceptions and **transforms** to use case results.

```python
class PlaceOrderUseCase:
    """Use case for placing orders."""

    async def execute(self, command: PlaceOrderCommand) -> OrderId:
        """Place a new order."""
        try:
            async with self._unit_of_work:
                portfolio = await self._portfolio_repo.get_active()

                try:
                    order = portfolio.place_order(command.to_domain())
                except ValidationError as e:
                    raise PlaceOrderValidationError(str(e)) from e

                await self._order_repo.save(order)
                await self._event_bus.publish(OrderCreated(order=order))

                return order.id

        except DatabaseError as e:
            logger.error("DatabaseError during order placement", extra={"order": command.to_dict()})
            raise OrderExecutionError("Temporary database issue, please retry") from e
        except CacheError as e:
            logger.warning("Cache miss during order placement", exc_info=True)
            # Continue despite cache error (eventual consistency)
            pass
```

### 3.3 Infrastructure Layer

Infrastructure layer **wraps** external failures and **translates** to domain exceptions.

```python
class SQLAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy implementation of Order repository."""

    async def save(self, order: Order) -> None:
        """Save order to database."""
        try:
            model = self._to_model(order)
            self._session.add(model)
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise DatabaseError(message="Database integrity check failed") from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise DatabaseError(message=f"Database operation failed: {e}") from e
```

### 3.4 Presentation Layer

Presentation layer **translates** domain exceptions to HTTP/Telegram responses.

```python
# presentation/api/v1/trading/router.py
from fastapi import HTTPException

@router.post("/orders", response_model=OrderResponse)
async def place_order(
    request: PlaceOrderRequest,
    use_case: PlaceOrderUseCase = Depends(get_place_order_use_case),
) -> OrderResponse:
    """Place a new trading order."""
    try:
        command = PlaceOrderCommand.from_request(request)
        order_id = await use_case.execute(command)
        return OrderResponse(order_id=order_id, status="open")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message) from e
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=e.user_message) from e
    except OrderRejectedError as e:
        raise HTTPException(status_code=400, detail=e.user_message) from e
    except ExchangeAPIError as e:
        logger.error("Failed to place order", exc_info=True, extra={"user_message": e.user_message})
        raise HTTPException(status_code=503, detail=e.user_message) from e


# presentation/telegram/handlers.py
@router.message(Command("buy"))
async def handle_buy_command(message: Message) -> None:
    """Handle /buy command."""
    try:
        command = parse_buy_command(message)
        await bot.trading_service.place_order(command)
        await message.reply("✅ Order placed successfully")
    except ValidationError as e:
        await message.reply(f"❌ Invalid order: {e.message}")
    except InsufficientBalanceError as e:
        await message.reply(f"❌ {e.user_message}")
    except OrderRejectedError as e:
        await message.reply(f"❌ {e.user_message}")
    except Exception as e:
        logger.error("Unexpected error in buy command", exc_info=True)
        await message.reply("❌ An unexpected error occurred. Please contact support.")
```

## 4. Error Recovery Strategies

### 4.1 Retry with Exponential Backoff

```python
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

@retry(
    retry=retry_if_exception_type(ExchangeAPIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    reraise=True,
)
async def fetch_market_data(symbol: Symbol) -> MarketData:
    """Fetch market data with auto-retry on transient failures."""
    ...
```

### 4.2 Circuit Breaker

```python
class CircuitBreaker:
    """Circuit breaker for external service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure: float = 0.0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        if self._state == "OPEN":
            if time.monotonic() - self._last_failure > self._recovery_timeout:
                self._state = "HALF_OPEN"
            else:
                raise ExchangeAPIError(exchange="circuit_breaker_open", error="Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self._failure_count = 0
        self._state = "CLOSED"

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
```

```python
# Usage
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

async def fetch_with_circuit_breaker(symbol: Symbol) -> MarketData:
    async def _fetch() -> MarketData:
        return await exchange_client.fetch_ticker(symbol)

    return await circuit_breaker.call(_fetch)
```

### 4.3 Graceful Degradation

```python
class MarketDataService:
    """Market data service with degraded operation modes."""

    async def get_candles(self, symbol: Symbol, timeframe: Timeframe) -> list[Candle]:
        try:
            return await self._cache.get_candles(symbol, timeframe)
        except CacheError:
            logger.warning("Cache unavailable, falling back to database")

        try:
            return await self._repo.get_candles(symbol, timeframe)
        except DatabaseError:
            logger.error("Database unavailable, falling back to live fetch")

        try:
            return await self._exchange.fetch_candles(symbol, timeframe)
        except ExchangeAPIError as e:
            raise MarketDataUnavailableError(
                symbol=symbol,
                timeframe=timeframe,
                reason=str(e),
            ) from e
```

## 5. Global Exception Handlers

### 5.1 FastAPI Exception Handlers

```python
# presentation/api/middleware.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(TradingError)
    async def trading_error_handler(request: Request, exc: TradingError) -> JSONResponse:
        """Handle all custom TradingError exceptions."""
        status_code = 400 if not exc.retryable else 503
        logger.info(
            "TradingError handled",
            extra={
                "error_code": exc.code,
                "error_message": exc.message,
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.user_message or exc.message,
                    "details": exc.details,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors with domain context."""
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.critical(
            "Unhandled exception",
            exc_info=True,
            extra={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
```

### 5.2 Telegram Error Handlers

```python
# presentation/telegram/handlers.py
@router.error()
async def error_handler(event: ErrorEvent) -> bool:
    """Global Telegram error handler."""
    logger.error(
        "Telegram handler error",
        exc_info=True,
        extra={"update": event.update.model_dump() if event.update else None},
    )
    # Reply to user if possible
    if isinstance(event.event, Message):
        await event.event.reply("❌ An unexpected error occurred. Please try again.")
    return True  # Suppress default error handling
```

## 6. Async Error Handling

### 6.1 Task Group Error Aggregation

```python
import asyncio

async def execute_parallel_tasks(commands: list[Command]) -> list[Result]:
    """Execute multiple commands in parallel with error aggregation."""
    results = []
    errors = []

    async def execute_one(cmd: Command) -> Result:
        try:
            return await execute_command(cmd)
        except Exception as e:
            errors.append((cmd.id, e))
            raise

    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(execute_one(cmd)) for cmd in commands]
            results = [t.result() for t in tasks]
    except ExceptionGroup as eg:
        # Aggregate all errors from task group
        for exc in eg.exceptions:
            logger.error("Parallel execution failed", exc_info=True, extra={"error": str(exc)})
        # Re-raise with aggregated context
        raise ParallelExecutionError(
            message=f"One or more commands failed: {len(errors)}/{len(commands)}",
            details={"errors": [(cmd_id, str(e)) for cmd_id, e in errors]},
        ) from eg

    return results
```

### 6.2 Timeout Handling

```python
import asyncio

async def execute_with_timeout(coro, timeout: float) -> T:
    """Execute coroutine with explicit timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("Operation timed out", extra={"timeout": timeout})
        raise OperationTimeoutError(f"Operation exceeded {timeout}s timeout") from None
```

### 6.3 Cancellation Safety

```python
async def cancellable_operation(progress_callback) -> Result:
    """Operation that handles cancellation gracefully."""
    for step in steps:
        if asyncio.current_task().cancelled():
            logger.info("Operation cancelled, cleaning up")
            await cleanup()
            raise asyncio.CancelledError()
        result = await step()
        await progress_callback(result)
    return result
```

## 7. Business Rule Violations

### 7.1 Invariant Enforcement

Business invariants MUST be checked at aggregate root level.

```python
class Portfolio:
    """Portfolio aggregate root."""

    def place_order(self, command: PlaceOrderCommand) -> Order:
        """Place a new order within portfolio invariants."""
        # Invariant: Symbol must be known
        if not self.is_symbol_known(command.symbol):
            raise ValidationError(
                message=f"Unknown symbol: {command.symbol}",
                code="UNKNOWN_SYMBOL",
            )

        # Invariant: Sufficient balance
        if not self._has_sufficient_balance(command):
            raise InsufficientBalanceError(
                required=command.quantity * command.limit_price,
                available=command.balance,
                currency=command.currency,
            )

        # Invariant: Risk limit not exceeded
        risk_assessment = self._risk_service.assess_order_risk(command)
        if not risk_assessment.is_within_limits:
            raise RiskLimitExceededError(
                limit_type=risk_assessment.limit_type,
                current=risk_assessment.current_value,
                limit=risk_assessment.limit_value,
            )

        return Order.create(command)
```

### 7.2 Fail-Fast Validation

Validate command/request at entry point:

```python
class PlaceOrderCommand:
    @classmethod
    def from_request(cls, request: PlaceOrderRequest) -> Self:
        try:
            return cls(
                symbol=Symbol(request.symbol),
                side=OrderSide(request.side),
                quantity=Quantity(request.quantity),
                order_type=OrderType(request.order_type),
                limit_price=Price(request.limit_price) if request.limit_price else None,
            )
        except ValueError as e:
            raise ValidationError(message=f"Invalid order parameters: {e}") from e
```

## 8. Logging with Errors

### 8.1 Error Context Collection

```python
def log_error_with_context(
    logger: logging.Logger,
    exc: BaseException,
    **context,
) -> None:
    """Log error with full context and skip stack trace for user errors."""
    log_data = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        **context,
    }

    if isinstance(exc, (UserError, DomainError)):
        # User-caused error - log at INFO, no stack trace
        logger.info("User error", extra=log_data)
    else:
        # System error - log at ERROR with traceback
        logger.error("System error", extra=log_data, exc_info=True)
```

### 8.2 Sentry Integration (Future)

```python
import sentry_sdk

def setup_error_monitoring() -> None:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
    )

    # Add custom breadcrumbs
    def before_send(event, hint):
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            if isinstance(exc_value, (SensitiveDataError, AuthenticationError)):
                return None  # Skip sending sensitive errors
        return event
```

## 9. Quiet Exceptions

### 9.1 Acceptable Silent Failures

Only these exceptions may be logged without raising:

```python
# Cache miss (expected, not an error)
try:
    cached = await cache.get(key)
except CacheError:
    logger.debug("Cache miss, falling back to source")
    cached = None

# Rate limit hit with retry (transient, retries will happen)
try:
    result = await rate_limited_call()
except RateLimitError as e:
    logger.warning(
        "Rate limit hit, will retry",
        extra={"wait": e.retry_after},
    )
    # Return default/sentinel or retry automatically
```

### 9.2 Forbidden Silent Failures

These MUST always propagate:

```python
# NEVER do this
try:
    result = await critical_operation()
except Exception:
    pass  # FORBIDDEN - silent failure

# ALWAYS do this
try:
    result = await critical_operation()
except SpecificError as e:
    logger.error("Critical operation failed", exc_info=True)
    raise CriticalError("Operation failed") from e
```

## 10. Health Check Failures

### 10.1 Component Health Status

```python
class HealthStatus:
    """Health check result."""

    def __init__(self, component: str, healthy: bool, details: dict | None = None):
        self.component = component
        self.healthy = healthy
        self.details = details or {}
        self.checked_at = datetime.now(timezone.utc)

    @property
    def status(self) -> str:
        return "healthy" if self.healthy else "unhealthy"


async def check_database_health() -> HealthStatus:
    """Check database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return HealthStatus(component="database", healthy=True)
    except Exception as e:
        logger.error("Database health check failed", exc_info=True)
        return HealthStatus(
            component="database",
            healthy=False,
            details={"error": str(e)},
        )
```

### 10.2 Health Check Aggregation

```python
async def get_system_health() -> dict:
    """Check all system components."""
    checks = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_exchange_health(),
        check_ai_provider_health(),
    )

    overall = all(check.healthy for check in checks)
    return {
        "status": "healthy" if overall else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {c.component: c.details for c in checks},
    }
```
