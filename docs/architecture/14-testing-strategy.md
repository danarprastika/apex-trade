# Testing Strategy

## Test Pyramid

```
                /\
               /  \
              / E2E \         10%
             /______\
            /        \
           / Integr.  \       20%
          /____________\
         /              \
        /    Unit Tests    \   70%
       /____________________\
```

| Test Type | Target % | Scope | Speed | Cost |
|-----------|----------|-------|-------|------|
| Unit | 70% | Single classes/functions | Fast (<100ms) | Low |
| Integration | 20% | Multiple components | Medium (<1s) | Medium |
| E2E | 10% | Full system | Slow (<10s) | High |

## Testing Frameworks

### Backend
- pytest: Test runner and framework
- pytest-mock: Mocking and patching
- pytest-asyncio: Async test support
- pytest-cov: Coverage reporting
- factory-boy: Test data factories
- faker: Random test data generation
- testcontainers: Database/integration testing

### Frontend
- Vitest: Unit and integration tests
- React Testing Library: Component testing
- @testing-library/user-event: User interaction simulation
- MSW (Mock Service Worker): API mocking
- Playwright: E2E browser testing

## Unit Testing Conventions

### Test Structure (AAA Pattern)
- Arrange: Set up test data and conditions
- Act: Execute the function/method under test
- Assert: Verify the results

### Naming Conventions
- test_{function_name} for functions
- test_{class_name}_{method_name} for methods
- Test{ClassName} for test classes
- Descriptive names: test_calculate_balance_returns_zero_for_empty_portfolio

### Mocking Strategy
- Mock external dependencies (exchanges, AI APIs)
- Use unittest.mock.AsyncMock for async functions
- Prefer dependency injection for testability
- Do not mock internal components

### Edge Cases
- Empty inputs
- Boundary values
- Null/None handling
- Error conditions
- Concurrent access (where applicable)

## Integration Testing

### Database Tests
- Use TestContainers for PostgreSQL
- Run migrations in test setup
- Test repository implementations
- Transaction rollback after each test

### External Service Tests
- Mock external APIs (exchanges, AI)
- Use recorded responses (VCR)
- Test circuit breakers
- Test retry logic

### API Tests
- Test against running server
- Use TestClient for FastAPI
- Test authentication flows
- Test error responses

### Test Data Management
- Session-scoped database containers
- Schema setup/teardown per test
- Factory pattern for test entities
- Cleanup after each test

## E2E Testing

### Scope
- Full user workflows (register, trade, view portfolio)
- Critical paths (order placement, risk checks)
- Cross-service interactions

### Frontend E2E
- Playwright for browser automation
- Test against staging environment
- Visual regression testing (future)
- Accessibility testing (future)

### Backend E2E
- API workflow tests
- WebSocket connection tests
- Bot interaction tests

### Test Environment
- Separate staging environment
- Realistic data (anonymized production)
- No production dependencies

## Coverage Requirements

### Thresholds

| Module | Minimum Coverage | Target Coverage |
|--------|-----------------|-----------------|
| Domain | 90% | 95% |
| Application | 85% | 90% |
| Infrastructure | 70% | 80% |
| Presentation | 60% | 70% |
| Overall | 80% | 85% |

### Enforcement
- Block merge on coverage drop
- Coverage report in CI
- Exclude test files from coverage
- Exclude generated files

### Exclusions
- __init__.py files
- Test files themselves
- Abstract base classes (if not testable)
- Type stub files

## CI Test Pipeline

### Stages
1. Lint: Ruff check, mypy type check
2. Unit Tests: Fast unit test suite
3. Integration Tests: Database and external service tests
4. E2E Tests: Full system tests (staging)
5. Coverage Report: Generate and upload

### Parallelization
- Unit tests: Parallel execution
- Integration tests: Sequential (database contention)
- E2E tests: Parallel (isolated environments)

### Flaky Test Handling
- Retry failed tests (max 2 retries)
- Quarantine flaky tests for investigation
- Alert on flaky test patterns

## Performance Testing

### Load Testing
- Target: 100 requests/second sustained
- Tool: Locust or k6
- Scenario: Mixed read/write workload

### Stress Testing
- Find breaking point
- Identify bottlenecks
- Validate graceful degradation

### Soak Testing
- 24-hour continuous load
- Memory leak detection
- Connection pool exhaustion check
