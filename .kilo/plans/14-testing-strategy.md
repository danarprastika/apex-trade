# Testing Strategy

## 1. Testing Philosophy

Testing is an integral part of the development process, not an afterthought. QuantX AI employs a multi-layered testing strategy to ensure reliability, correctness, and maintainability.

## 2. Test Pyramid

```
        ┌─────────────┐
        │   E2E Tests │  (Slow, few)
        ├─────────────┤
        │  Integration │  (Medium, some)
        ├─────────────┤
        │     Unit     │  (Fast, many)
        └─────────────┘
```

### 2.1 Unit Tests (70%)
- Test individual classes, functions, methods
- Fast execution (< 1s per 100 tests)
- Isolated from external dependencies
- Mock all external interactions

### 2.2 Integration Tests (25%)
- Test component interactions
- Database, cache, external API integrations
- Slow execution (database setup/teardown)
- Use testcontainers or ephemeral databases

### 2.3 E2E Tests (5%)
- Test complete user workflows
- Full system deployment
- Most expensive to maintain
- Focus on critical paths only

## 3. Test Documentation

Every test file MUST have a docstring explaining its purpose:

```python
"""Test the Order aggregate.

This test module verifies:
1. Order creation with valid parameters succeeds
2. Order creation with invalid parameters raises ValueError
3. Order.fill() correctly updates order state
4. Order.cancel() validates order state before cancellation
5. Order.is_active() returns correct status

Run with: pytest tests/unit/domain/test_order.py
"""

import pytest
from decimal import Decimal
from src.domain.entities import Order
from src.domain.value_objects import OrderSide, OrderType, Price, Quantity
```

## 4. Test Organization

### 4.1 Unit Tests Structure

```
tests/unit/
├── __init__.py
├── conftest.py                     # Shared unit test fixtures
├── domain/
│   ├── __init__.py
│   ├── test_entities.py            # Test Order, Position, Portfolio
│   ├── test_value_objects.py       # Test Price, Quantity, Symbol
│   ├── test_aggregates.py          # Test PortfolioAggregate
│   ├── test_domain_services.py     # Test RiskCalculationService
│   └── test_repositories.py        # Test repository interfaces
├── application/
│   ├── __init__.py
│   ├── use_cases/
│   │   ├── test_place_order.py
│   │   ├── test_cancel_order.py
│   │   ├── test_execute_strategy.py
│   │   └── test_get_portfolio.py
│   ├── services/
│   │   ├── test_trading_service.py
│   │   ├── test_market_data_service.py
│   │   └── test_risk_monitoring.py
│   └── events/
│       ├── test_order_event_handlers.py
│       └── test_trade_event_handlers.py
└── infrastructure/
    ├── __init__.py
    ├── repositories/
    │   ├── test_order_repository.py
    │   └── test_market_data_repository.py
    ├── services/
    │   ├── test_ai_provider.py
    │   ├── test_exchange_adapter.py
    │   └── test_telegram_bot.py
    └── cache/
        └── test_redis_cache.py
```

### 4.2 Integration Tests Structure

```
tests/integration/
├── __init__.py
├── conftest.py                         # Shared integration fixtures (db, redis)
├── test_database/
│   ├── test_connection.py
│   ├── test_migrations.py
│   └── test_transactions.py
├── test_repositories/
│   ├── test_order_repository_integration.py
│   └── test_market_data_repository_integration.py
├── test_api/
│   ├── test_trading_endpoints.py
│   ├── test_portfolio_endpoints.py
│   └── test_health_endpoints.py
├── test_websocket/
│   └── test_market_data_stream.py
└── test_external/
    ├── test_exchange_integration.py
    ├── test_ai_provider_integration.py
    └── test_telegram_integration.py
```

### 4.3 E2E Tests Structure

```
tests/e2e/
├── __init__.py
├── conftest.py
├── test_order_lifecycle.py      # Place → Fill → Close workflow
├── test_portfolio_reporting.py  # Balance tracking, P&L calculation
└── test_risk_alerting.py        # Risk monitoring, alert delivery
```

## 5. Markdown Test Documentation

### 5.1 Test Case Documentation

Every test case must be documented in Markdown format (either in docstring or separate file):

```python
"""Test: Order placement with insufficient balance.

**Preconditions**:
- Portfolio with 1000 USDT balance
- BTC/USDT price at 30000

**Test Steps**:
1. Create PlaceOrderCommand with 0.1 BTC (requires 3000 USDT)
2. Execute PlaceOrderUseCase

**Expected Result**:
- InsufficientBalanceError is raised
- Order not saved to database
- User-friendly error message returned

**Actual Result**:
(In test execution output)

**Notes**:
This is a regression test for issue #42.
"""
def test_place_order_insufficient_balance() -> None:
    ...
```

### 5.2 Test Coverage Documentation

```markdown
# Test Coverage Report (Generated)

## Unit Test Coverage
- Domain Layer: 95%
  - Entities: 100%
  - Value Objects: 100%
  - Domain Services: 90%
  - Repositories (interfaces): 85%

- Application Layer: 90%
  - Use Cases: 92%
  - Services: 88%
  - Event Handlers: 85%

- Infrastructure Layer: 75%
  - Repositories: 80%
  - External Services: 70%

## Integration Test Coverage
- API Endpoints: 85%
- Database Operations: 80%
- External Integrations: 60%

## E2E Test Coverage
- Critical Paths: 90%
```

## 6. Test Fixtures

### 6.1 Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from uuid import uuid4
from decimal import Decimal
from src.domain.value_objects import Price, Quantity, Symbol
from src.domain.entities import Order, Position, Portfolio
from src.infrastructure.database.engine import async_session_maker

@pytest.fixture
def btc_symbol() -> Symbol:
    return Symbol("BTC/USDT")

@pytest.fixture
def sample_price() -> Price:
    return Price(Decimal("30000"))

@pytest.fixture
def sample_quantity() -> Quantity:
    return Quantity(Decimal("0.1"))

@pytest.fixture
def sample_order(btc_symbol, sample_price, sample_quantity) -> Order:
    return Order(
        id=uuid4(),
        symbol=btc_symbol,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=sample_quantity,
        limit_price=sample_price,
    )

@pytest_asyncio.fixture
async def db_session():
    """Create test database session."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()
```

### 6.2 Mock Fixtures

```python
@pytest.fixture
def mock_order_repository():
    """Mock OrderRepository for unit tests."""
    from unittest.mock import AsyncMock, MagicMock
    mock = MagicMock(spec=OrderRepository)
    mock.save = AsyncMock()
    mock.find_by_id = AsyncMock(return_value=None)
    return mock

@pytest.fixture
def mock_exchange_client():
    """Mock CCXT exchange client."""
    from unittest.mock import AsyncMock, MagicMock
    mock = MagicMock()
    mock.fetch_ticker = AsyncMock(return_value={
        "last": 30000.0,
        "bid": 29999.0,
        "ask": 30001.0,
    })
    return mock
```

## 7. Mocking Strategy

### 7.1 Mock External Services

```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.mark.asyncio
async def test_place_order_with_mock_exchange():
    """Test order placement with mocked exchange."""
    mock_exchange = MagicMock(spec=ExchangeClient)
    mock_exchange.create_order = AsyncMock(return_value={
        "id": "exchange_order_123",
        "status": "open",
    })

    use_case = PlaceOrderUseCase(
        exchange=mock_exchange,
        ...
    )

    result = await use_case.execute(command)
    mock_exchange.create_order.assert_called_once()
    assert result.order_id is not None
```

### 7.2 Unmock Pure Domain Logic

Domain layer tests should have NO mocks - test the real logic.

```python
def test_order_calculation():
    """Test pure domain logic without mocks."""
    order = Order(
        id=uuid4(),
        quantity=Decimal("1.5"),
        price=Price(Decimal("100")),
    )

    # Calculate value directly
    expected = Decimal("150")
    assert order.total_value() == expected
```

### 7.3 Mocking Patterns

```python
# AsyncMock for async functions
mock_service.fetch_data = AsyncMock(return_value=[...])

# MagicMock for class instances
mock_repo = MagicMock(spec=OrderRepository)
mock_repo.save = AsyncMock()
mock_repo.find_by_id = AsyncMock(return_value=sample_order)

# Patch for dependency override
with patch("src.infrastructure.exchanges.ccxt_adapter.ccxt") as mock_ccxt:
    mock_ccxt.binance.return_value.fetch_ticker.return_value = {...}
    # ... test code
```

## 8. Test Data Management

### 8.1 Test Data Builders

```python
class OrderBuilder:
    """Fluent builder for creating test Order objects."""

    def __init__(self):
        self._id = uuid4()
        self._symbol = Symbol("BTC/USDT")
        self._side = OrderSide.BUY
        self._quantity = Quantity(Decimal("0.1"))
        self._price = Price(Decimal("30000"))

    def with_symbol(self, symbol: str) -> Self:
        self._symbol = Symbol(symbol)
        return self

    def with_quantity(self, quantity: Decimal) -> Self:
        self._quantity = Quantity(quantity)
        return self

    def with_price(self, price: Decimal) -> Self:
        self._price = Price(price)
        return self

    def build(self) -> Order:
        return Order(
            id=self._id,
            symbol=self._symbol,
            side=self._side,
            order_type=OrderType.LIMIT,
            quantity=self._quantity,
            limit_price=self._price,
        )


# Usage in tests
order = OrderBuilder().with_symbol("ETH/USDT").with_price(2000).build()
```

### 8.2 Database Fixtures

```python
@pytest_asyncio.fixture
async def populated_database(db_session):
    """Database with test data loaded."""
    from tests.fixtures import load_test_fixtures
    await load_test_fixtures(db_session, "tests/fixtures/test_data.json")
    yield db_session
    await db_session.rollback()
```

### 8.3 Test Data Cleanup

```python
@pytest_asyncio.fixture(autouse=True)
async def cleanup_after_test(db_session):
    """Ensure test isolation by rolling back after each test."""
    yield
    await db_session.rollback()
```

## 9. CI/CD Testing Pipeline

### 9.1 GitHub Actions Test Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install poetry
      - run: poetry install --with dev
      - run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

  linting:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install ruff
      - run: ruff check src/
      - run: ruff format src/ --check

  type_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install mypy
      - run: mypy src/

  integration_tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: quantx
          POSTGRES_PASSWORD: quantx
          POSTGRES_DB: quantx_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd redis-cli ping
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql+asyncpg://quantx:quantx@localhost:5432/quantx_test
      REDIS_URL: redis://localhost:6379/0
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install poetry
      - run: poetry install --with dev
      - run: pytest tests/integration/ -v
```

### 9.2 Coverage Requirements

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-ra -q --cov=src --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]
```

**Coverage Thresholds**:
- Unit tests: 80% minimum, 95% target
- Integration tests: 70% minimum
- E2E tests: Critical paths 100%

### 9.3 Test Parallelization

```bash
pytest tests/ -n auto  # Use pytest-xdist for parallel execution
```

## 10. Test Naming Conventions

```python
# Pattern: test_<method>_<condition>_<expected_result>
def test_order_create_with_valid_params_succeeds() -> None:
    ...

def test_order_create_with_negative_quantity_raises_error() -> None:
    ...

def test_order_fill_when_already_filled_raises_error() -> None:
    ...

def test_portfolio_calculate_pnl_with_no_positions_returns_zero() -> None:
    ...
```

## 11. Frontend Testing

### 11.1 React Testing Library

```typescript
// Test: Order form submission
import { render, screen, fireEvent } from "@testing-library/react";
import { OrderForm } from "./OrderForm";

describe("OrderForm", () => {
  it("submits order when valid", async () => {
    const onSubmit = jest.fn();
    render(<OrderForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Quantity"), {
      target: { value: "0.1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /buy/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
  });

  it("shows error when quantity is zero", () => {
    render(<OrderForm onSubmit={jest.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /buy/i }));
    expect(screen.getByText("Quantity must be > 0")).toBeInTheDocument();
  });
});
```

### 11.2 Component Test Coverage

```
Component Test Requirements:
- UI components: 100%
- Hooks: 100%
- Pages: 80%
- Utilities: 90%
```

### 11.3 E2E Frontend Testing (Playwright)

```typescript
// test/dashboard.spec.ts
import { test, expect } from "@playwright/test";

test("user can view portfolio dashboard", async ({ page }) => {
  await page.goto("http://localhost:5173");
  await expect(page.locator("[data-testid='portfolio-value']")).toBeVisible();
  await expect(page.locator("[data-testid='position-list']")).toContainText("BTC/USDT");
});
```

## 12. Test Configuration

### 12.1 pytest.ini

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -ra
    -q
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
    --strict-markers
    --strict-config
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (database, external services)
    e2e: End-to-end tests (full system)
    slow: Tests taking > 1 second
```

### 12.2 Test Fixtures

```python
@pytest.fixture(scope="session")
def event_loop():
    """Create single event loop for entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

## 13. Special Test Types

### 13.1 Property-Based Testing (Hypothesis)

```python
from hypothesis import given, strategies as st

@given(st.decimals(min_value=0, max_value=1000000, places=2))
def test_order_total_value_calculation(price):
    """Property: total_value = quantity * price."""
    order = OrderBuilder().with_price(Price(price)).build()
    assert order.total_value() == order.quantity * order.price
```

### 13.2 Contract Testing

```python
# Contract tests verify API endpoint schema
import schemathesis

schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api_contract(case):
    response = case.call()
    case.validate_response(response)
```

### 13.3 Snapshot Testing

```python
from syrupy import snapshot

def test_order_response_schema(snapshot):
    request = PlaceOrderRequest(...)
    response = PlaceOrderResponse.from_request(request)
    assert response == snapshot
```

## 14. Test Data Management

### 14.1 Fake Data Generator

```python
import faker

fake = faker.Faker()

def generate_test_order() -> Order:
    return Order(
        id=uuid4(),
        symbol=Symbol(fake.currency_code() + "/USD"),
        side=random.choice([OrderSide.BUY, OrderSide.SELL]),
        quantity=Quantity(fake.pydecimal(min_value=0.01, max_value=10)),
        price=Price(fake.pydecimal(min_value=100, max_value=100000)),
    )
```

### 14.2 Test Database Isolation

```python
# Use separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://quantx:quantx@localhost:5432/quantx_test"

# Or in-memory SQLite for faster tests
# DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

**Recommendation**: Use PostgreSQL via testcontainers or per-test tmpfs.

## 15. Test Environment Variables

```python
# .env.test
QUANTX_ENV=test
QUANTX_LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://quantx:quantx@localhost:5432/quantx_test
REDIS_URL=redis://localhost:6379/1
```

## 16. Test Monitoring

- CI coverage graph (Codecov or similar)
- Flaky test tracking
- Test execution time regression detection
- Failure trend analysis
