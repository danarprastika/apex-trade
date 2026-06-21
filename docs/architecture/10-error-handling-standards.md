# Error Handling Standards

## Custom Exception Hierarchy

### Base Exceptions

DomainException (ABC)
+-- ValidationException
¦   +-- InvalidSymbolException
¦   +-- InvalidPriceException
¦   +-- InvalidQuantityException
¦   +-- InsufficientFundsException
+-- BusinessRuleException
¦   +-- TradingNotAllowedException
¦   +-- MarketClosedException
¦   +-- PositionLimitExceededException
+-- TradingException
¦   +-- OrderFailedException
¦   +-- OrderCancelledException
¦   +-- ExchangeConnectionException
+-- RiskException
¦   +-- RiskLimitExceededException
¦   +-- DrawdownLimitExceededException
+-- NotFoundException
    +-- PortfolioNotFoundException
    +-- StrategyNotFoundException
    +-- SymbolNotFoundException

InfrastructureException (ABC)
+-- DatabaseException
¦   +-- ConnectionException
¦   +-- QueryException
+-- CacheException
¦   +-- RedisConnectionException
¦   +-- CacheMissException
+-- ExternalApiException
¦   +-- RateLimitExceededException
¦   +-- AuthenticationException
¦   +-- ServiceUnavailableException
+-- ConfigurationException

ApplicationException (ABC)
+-- UseCaseException
+-- CommandException

## Error Propagation Rules

### Rule 1: Domain Exceptions Bubble Up
- Domain exceptions are caught by Application layer
- Wrapped in UseCaseException if needed
- Never let Domain exceptions escape to Presentation

### Rule 2: Infrastructure Exceptions Wrapped
- All infrastructure exceptions wrapped in Application layer
- Preserve original exception as cause
- Log at wrapping point

### Rule 3: Presentation Layer Maps to HTTP
- Application exceptions mapped to HTTP status codes
- Domain exceptions translated to user-friendly messages
- Infrastructure details never exposed to user

### Rule 4: No Silent Failures
- Every exception must be logged
- Every exception must be either handled or re-raised
- No bare except: clauses

## HTTP Status Code Mapping

| Exception Type | HTTP Status | Description |
|----------------|-------------|-------------|
| ValidationException | 400 | Bad Request - Invalid input |
| NotFoundException | 404 | Not Found - Resource missing |
| BusinessRuleException | 422 | Unprocessable Entity - Business rule violated |
| RiskException | 422 | Unprocessable Entity - Risk limit hit |
| AuthenticationException | 401 | Unauthorized - Invalid credentials |
| AuthorizationException | 403 | Forbidden - Insufficient permissions |
| RateLimitExceededException | 429 | Too Many Requests |
| ExternalApiException | 502 | Bad Gateway - Upstream failure |
| DatabaseException | 500 | Internal Server Error |
| InfrastructureException | 500 | Internal Server Error |
| UnexpectedException | 500 | Internal Server Error |

## Retry Policies

### Exchange APIs
- Strategy: Exponential backoff
- Max Retries: 5
- Initial Delay: 1 second
- Backoff Factor: 2
- Jitter: +/-20%
- Retry On: 5xx, network errors, timeouts
- Do Not Retry: 4xx (except 429)

### AI APIs
- Strategy: Immediate fallback to alternative provider
- Max Retries: 2 (primary provider only)
- Fallback: OpenRouter if Gemini fails
- Timeout: 30 seconds per attempt

### Database
- Strategy: Fixed retry with backoff
- Max Retries: 3
- Delay: 0.5s, 1s, 2s
- Retry On: Connection errors, deadlocks
- Do Not Retry: Integrity errors, constraint violations

### Cache (Redis)
- Strategy: Cache-aside, silent failure
- Max Retries: 1
- Fallback: Proceed without cache
- Log: Warning on cache failure

## Circuit Breaker Pattern

### Configuration

| Service | Failure Threshold | Recovery Timeout | Half-Open Requests |
|---------|------------------|------------------|-------------------|
| Exchange APIs | 5 failures | 60 seconds | 1 |
| AI APIs | 3 failures | 30 seconds | 1 |
| External Notifications | 10 failures | 120 seconds | 2 |

### States
1. CLOSED: Normal operation, requests pass through
2. OPEN: Circuit tripped, requests fail immediately
3. HALF-OPEN: Test request allowed, success closes circuit

### Implementation
- Track consecutive failures per service
- Circuit opens when threshold reached
- Half-open after recovery timeout
- Metrics: failure count, last failure time, state transitions

## Global Exception Handler

### Responsibilities
1. Catch all unhandled exceptions
2. Log with full context
3. Map to appropriate HTTP response
4. Sanitize error messages for users
5. Include correlation ID in response

### Response Format
- error.code: Machine-readable error code
- error.message: User-friendly message
- error.correlation_id: Request tracking ID
- error.details: Optional additional context

## Timeout Configuration

| Service | Connect Timeout | Read Timeout | Total Timeout |
|---------|----------------|--------------|---------------|
| Exchange APIs | 5s | 10s | 30s |
| AI APIs | 5s | 30s | 60s |
| Database | 5s | 30s | 60s |
| Cache | 2s | 5s | 10s |
| Internal Services | 2s | 5s | 15s |

## Graceful Degradation

### Strategies
1. Fallback Data: Use cached data when fresh data unavailable
2. Feature Toggle: Disable non-critical features on failure
3. Queue for Retry: Queue failed operations for later retry
4. User Notification: Inform user of degraded service

### Degraded Modes
- Market Data: Use last known price (stale data warning)
- AI Strategy: Disable AI features, use manual trading
- Notifications: Queue notifications, deliver when recovered
- Reporting: Show cached reports with staleness indicator
