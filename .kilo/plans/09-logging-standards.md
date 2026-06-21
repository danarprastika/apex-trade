# Logging Standards

## 1. Logging Philosophy

Logging is a **first-class concern** in QuantX AI. Every action, decision, and external interaction is logged with structured data. Logs are not just for debugging—they serve as the audit trail, compliance record, and operational observability layer.

**Golden Rule**: If it cannot be explained from logs, it should not happen.

## 2. Structured Logging Architecture

### 2.1 JSON Logger for All Structured Logs

```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logging() -> None:
    """Configure structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
```

**Output format**:
```json
{
  "timestamp": "2025-01-15T14:30:22.123Z",
  "logger": "src.application.use_cases.place_order",
  "level": "INFO",
  "message": "Order placed successfully",
  "order_id": "abc-123",
  "symbol": "BTC/USDT",
  "side": "buy",
  "quantity": "0.1",
  "user_id": "user-456",
  "duration_ms": 245
}
```

### 2.2 Logger Naming Convention

Use module path as logger name:

```python
import logging

# In src/application/use_cases/place_order.py:
logger = logging.getLogger(__name__)
# Results in: src.application.use_cases.place_order

# Domain layer:
logger = logging.getLogger(__name__)
# Results in: src.domain.entities.order

# Infrastructure:
logger = logging.getLogger(__name__)
# Results in: src.infrastructure.exchanges.ccxt_adapter
```

**Hierarchical Categories**:
- `src.domain.*` - Domain logic
- `src.application.*` - Application orchestration
- `src.infrastructure.database.*` - Database operations
- `src.infrastructure.exchanges.*` - Exchange integrations
- `src.infrastructure.ai.*` - AI providers
- `src.presentation.api.*` - REST endpoints
- `src.presentation.telegram.*` - Telegram handlers
- `src.presentation.websocket.*` - WebSocket connections

## 3. Log Levels and Usage

### 3.1 Level Guide

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Development diagnostic info | Sparkline of raw API response |
| **INFO** | Business events | Order placed, trade executed |
| **WARNING** | Recoverable issues | Rate limit approaching |
| **ERROR** | Failures needing attention | API call failed |
| **CRITICAL** | System failures | DB connection lost |

### 3.2 Business Event Logging (INFO)

Mandatory INFO logs for all business events:

```python
# Order lifecycle events
logger.info("OrderPlaced", extra={
    "order_id": str(order.id),
    "symbol": order.symbol,
    "side": str(order.side),
    "quantity": str(order.quantity),
    "order_type": str(order.order_type),
    "portfolio_id": str(portfolio.id),
})

# Trade execution events
logger.info("TradeExecuted", extra={
    "trade_id": str(trade.id),
    "order_id": str(trade.order_id),
    "symbol": trade.symbol,
    "price": str(trade.price),
    "quantity": str(trade.quantity),
    "fee": str(trade.fee),
    "pnl": str(realized_pnl),
})

# Portfolio updates
logger.info("PortfolioValueUpdated", extra={
    "portfolio_id": str(portfolio.id),
    "total_value": str(total_value),
    "total_pnl": str(total_pnl),
    "daily_pnl": str(daily_pnl),
    "timestamp": datetime.now(timezone.utc).isoformat(),
})
```

### 3.3 Error Logging

```python
# Include context and preserve exception chain
try:
    order = await exchange.create_order(command.to_ccxt())
except ExchangeAPIError as e:
    logger.error(
        "OrderExecutionFailed",
        extra={
            "order_id": str(command.id),
            "symbol": command.symbol,
            "exchange": exchange.name,
            "error_code": e.code,
            "error_message": str(e),
            "retryable": e.retryable,
        },
        exc_info=True,
    )
    raise OrderExecutionError("Order placement failed") from e
```

**Key rules for ERROR logs**:
- Always include `exc_info=True` for exceptions
- Include all context that helps debugging
- Preserve exception chain with `raise ... from ...`

## 4. Correlation and Tracing

### 4.1 Correlation IDs

Every user-initiated request gets a unique correlation ID:

```python
import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id")

def set_correlation_id() -> str:
    correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id

# Access from anywhere in the call chain
correlation_id = correlation_id_var.get("unknown")
```

**Middleware injection**:
```python
class CorrelationIdMiddleware:
    async def __call__(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

### 4.2 Request Spanning

```python
import time
from contextvars import ContextVar

span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)
start_time_var: ContextVar[float | None] = ContextVar("start_time", default=None)

class SpanLogger:
    """Context manager for timing and logging spans."""

    def __init__(self, operation: str, **extra):
        self.operation = operation
        self.extra = extra
        self.span_id = str(uuid.uuid4())
        self.start_time: float | None = None

    async def __aenter__(self):
        span_id_var.set(self.span_id)
        start_time_var.set(time.perf_counter())
        logger.debug(f"SpanStart: {self.operation}", extra={
            "span_id": self.span_id,
            "operation": self.operation,
            **self.extra
        })
        return self

    async def __aexit__(self, *args):
        duration_ms = (time.perf_counter() - start_time_var.get()) * 1000
        logger.info(f"SpanEnd: {self.operation}", extra={
            "span_id": self.span_id,
            "operation": self.operation,
            "duration_ms": round(duration_ms, 2),
            "status": "success",
            **self.extra
        })
```

### 4.3 Usage Example

```python
async def execute(self, command: PlaceOrderCommand) -> OrderId:
    async with SpanLogger("PlaceOrder", symbol=command.symbol) as span:
        try:
            async with self._unit_of_work:
                order = self._portfolio.place_order(command)
                await self._order_repo.save(order)
                await self._event_bus.publish(OrderCreated(order=order))
                return order.id
        except Exception as e:
            span.extra["error"] = str(e)
            span.extra["status"] = "failed"
            raise
```

## 5. Sensitive Data Logging Rules

### 5.1 Data to NEVER Log

- API keys and tokens
- Passwords (any source)
- Private keys (crypto exchanges)
- Session tokens
- Full card numbers (future)

```python
def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive fields from log data."""
    sensitive_keys = {
        "api_key", "secret", "password", "token", "private_key",
        "telegram_bot_token", "gemini_api_key", "openrouter_api_key",
    }
    return {k: v for k, v in data.items()
            if k.lower() not in sensitive_keys}
```

### 5.2 Partial Masking

For rarely needed sensitive context:

```python
# OK - show last 4 digits only for debugging
logger.debug("API key configured", extra={
    "api_key_masked": api_key[-4:] + "****",
})

# OK - show key name and prefix
logger.debug("Exchange credentials", extra={
    "exchange": "binance",
    "api_key_prefix": api_key[:6] + "****",
})
```

## 6. Log Aggregation and Retention

### 6.1 Retention Policy

| Log Category | Retention | Reason |
|--------------|-----------|--------|
| Trade execution | 7 years | Regulatory compliance |
| Order history | 7 years | Regulatory compliance |
| System/app logs | 90 days | Operational debugging |
| DEBUG logs | 30 days | Development/debugging |
| Audit trail | 7 years | Compliance |

### 6.2 Storage Strategy
```
VPS Storage Layout:
/var/log/quantx/
├── app.log              # Current application logs (Docker stdout)
├── app.log.1.gz         # Rotated logs
├── errors.log           # Error-only logs for quick triage
├── trading/             # Per-day trading logs
│   ├── 2025-01-15.log
│   └── archive/
└── audit/               # Immutable audit trail
    └── 2025-Q1/
```

### 6.3 External Archival (Future)

For compliance-critical logs:
- Daily archival to object storage (MinIO or S3-compatible)
- Immutable storage with write-once-read-many (WORM)
- Automated lifecycle policies

## 7. Log Analysis and Monitoring

### 7.1 Key Metrics from Logs

```
Error Rate = ERROR + CRITICAL logs / minute
Latency P95 = 95th percentile of span durations
Trade Execution Time = Span duration for "PlaceOrder"
```

### 7.2 Alerting Triggers

| Alert Condition | Severity | Action |
|----------------|----------|--------|
| ERROR rate > 10/min | CRITICAL | Page on-call engineer |
| Market data gap > 30s | WARNING | Check exchange connectivity |
| Trade execution P95 > 5s | WARNING | Review exchange latency |
| Auth failures > 5/min | HIGH | Potential attack detected |
| DB connection pool > 90% | HIGH | Scale or optimize |

### 7.3 Log Pattern Examples

```python
# Failed order pattern: search for quick triage
# grep "OrderExecutionFailed" /var/log/quantx/app.log | tail -20

# High latency trades
# grep "PlaceOrder" /var/log/quantx/app.log | jq 'select(.duration_ms > 1000)'

# Daily trade volume
# grep "TradeExecuted" /var/log/quantx/app.log | jq -r '.timestamp' | cut -d'T' -f1 | sort | uniq -c
```

## 8. Application Logs

### 8.1 Startup Logging

```python
logger.info("Application starting", extra={
    "version": __version__,
    "environment": settings.environment,
    "python_version": sys.version,
    "pid": os.getpid(),
})

logger.info("Connecting to dependencies")
logger.info("Database connected", extra={"host": settings.db_host, "port": settings.db_port})
logger.info("Redis connected", extra={"host": settings.redis_host})
logger.info("Exchange connections initialized", extra={
    "exchanges": exchange_manager.list_exchanges()
})
logger.info("AI provider initialized", extra={"primary": "gemini", "fallback": "openrouter"})
logger.info("Telegram bot started", extra={"bot_username": bot_info.username})
```

### 8.2 Shutdown Logging

```python
async def shutdown() -> None:
    logger.info("Application shutting down", extra={
        "reason": "SIGTERM received",
    })
    # Graceful shutdown of components
    await exchange_manager.close_all()
    await event_bus.close()
    await database_engine.dispose()
    logger.info("Application shutdown complete")
```

## 9. External API Logging

### 9.1 Request/Response Logging

```python
class LoggingExchangeAdapter(CCXTExchangeAdapter):
    async def create_order(self, order: Order) -> ExchangeOrder:
        logger.debug("CCXT: Creating order", extra={
            "exchange": self._exchange_name,
            "symbol": order.symbol,
            "side": order.side,
            "type": order.type,
            "amount": str(order.quantity),
            "price": str(order.limit_price) if order.limit_price else None,
        })

        try:
            result = await self._exchange.create_order(
                symbol=order.symbol,
                type=order.type,
                side=order.side,
                amount=float(order.quantity),
                price=float(order.limit_price) if order.limit_price else None,
            )
            logger.debug("CCXT: Order created", extra={
                "exchange": self._exchange_name,
                "exchange_order_id": result.get("id"),
                "status": result.get("status"),
            })
            return result
        except Exception as e:
            logger.error("CCXT: Order creation failed", extra={
                "exchange": self._exchange_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }, exc_info=True)
            raise
```

### 9.2 Rate Limiting Logging

```python
class RateLimiter:
    async def acquire(self, endpoint: str) -> None:
        """Acquire permit for API call, logging rate limit status."""
        async with self._lock:
            available, reset_time = await self._check_rate_limit(endpoint)
            if available <= 0:
                wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
                logger.warning("RateLimitApproaching", extra={
                    "exchange": self._exchange_name,
                    "endpoint": endpoint,
                    "wait_seconds": round(wait_seconds, 2),
                    "reset_time": reset_time.isoformat(),
                })
                await asyncio.sleep(max(wait_seconds, 0))
```

### 9.3 AI Provider Logging

```python
class GeminiAIProvider:
    async def analyze_market(self, prompt: str) -> AIAnalysisResponse:
        logger.debug("AI: Analyzing market", extra={
            "provider": "gemini",
            "prompt_length": len(prompt),
        })

        try:
            response = await self._client.generate_content(prompt)
            parsed = self._parse_response(response.text)
            logger.info("AI: Analysis complete", extra={
                "provider": "gemini",
                "direction": parsed.direction,
                "confidence": parsed.confidence,
                "tokens_used": response.usage.total_tokens,
            })
            return parsed
        except Exception as e:
            logger.error("AI: Analysis failed", extra={
                "provider": "gemini",
                "error": str(e),
            }, exc_info=True)
            raise
```

## 10. Security and Audit Logging

### 10.1 Authentication Events

```python
# Successful Telegram auth
logger.info("UserAuthenticated", extra={
    "user_id": user_id,
    "auth_method": "telegram",
    "ip_address": request.client.host,
})

# Failed auth attempt
logger.warning("UserAuthenticationFailed", extra={
    "telegram_user_id": user_id,
    "reason": "invalid_token",
    "ip_address": request.client.host,
})
```

### 10.2 Authorization Events

```python
# Access denied
logger.warning("AccessDenied", extra={
    "user_id": user_id,
    "resource": f"/api/trading/orders/{order_id}",
    "action": "place_order",
    "reason": "insufficient_permissions",
    "portfolio_id": portfolio_id,
})
```

### 10.3 Sensitive Operations Log

```python
# Order placement (high-risk operation)
logger.info("OrderPlaced", extra={
    "order_id": str(order.id),
    "portfolio_id": str(order.portfolio_id),
    "symbol": order.symbol,
    "side": order.side,
    "quantity": str(order.quantity),
    "order_type": str(order.order_type),
    "price": str(order.limit_price) if order.limit_price else None,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "user_id": str(user_id),
})

# Configuration changes
logger.info("ConfigurationUpdated", extra={
    "user_id": str(user_id),
    "setting": setting_name,
    "old_value": old_value,
    "new_value": new_value,
    "timestamp": datetime.now(timezone.utc).isoformat(),
})
```

## 11. Environment Variable Control

### 11.1 Log Control via Environment Variables

```python
import os
import logging

LOG_LEVEL = os.getenv("QUANTX_LOG_LEVEL", "INFO").upper()
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging.basicConfig(level=LOG_LEVELS[LOG_LEVEL])

# Verbose component logging
if os.getenv("QUANTX_LOG_CCXT_DETAILED") == "true":
    ccxt_logger = logging.getLogger("src.infrastructure.exchanges.ccxt")
    ccxt_logger.setLevel(logging.DEBUG)
```

### 11.2 Correlation ID via Environment

```python
# For service-to-service calls
CORRELATION_ID = os.getenv("QUANTX_CORRELATION_ID", str(uuid.uuid4()))
correlation_id_var.set(CORRELATION_ID)
```

## 12. Log Output Destinations

### 12.1 Production Docker Output

```
Docker containers → stdout/stderr → docker.json log driver → Host file
```

Logs from all services collected centrally via Docker logging driver.

### 12.2 Local Development

```
Console output (JSON formatted)
File output (rotated) for persistent analysis
```

### 12.3 Log Rotation

```yaml
# docker-compose production logging
logging:
  driver: json-file
  options:
    max-size: "100m"
    max-file: "10"
```

## 13. Log Analysis Queries

### 13.1 Common Queries

```python
# jq or Python code to filter logs programmatically

# "Show all orders placed for symbol X"
grep '"symbol": "BTC/USDT"' | grep '"message": "OrderPlaced"'

# "Show failed trades with retry attempts"
grep '"message": "TradeExecutionFailed"' | jq '.retry_count > 0'

# "Daily error count"
grep '"level": "ERROR"' | jq -r '.timestamp[:10]' | sort | uniq -c | sort -nr

# "P95 order execution latency"
grep '"operation": "PlaceOrder"' | jq -r '.duration_ms' | sort -n | awk '{s[NR]=$1} END{print s[int(NR*0.95)]}'
```

## 14. Compliance and Audit Requirements

### 14.1 Immutable Audit Trail

Critical trading events logged to immutable storage:
- Order placement, modification, cancellation
- Trade execution
- Balance changes
- Strategy activation/deactivation
- Configuration changes

```python
# Audit event logging
logger.critical("AuditTrail: TradeExecuted", extra={
    "audit_trail": True,
    "immutable": True,
    "trade_id": str(trade.id),
    "order_id": str(order.id),
    "amount": str(trade.quantity),
    "price": str(trade.price),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    # ... full context
})
```

### 14.2 Log Integrity

- Logs NEVER modified after creation
- Timestamps in UTC with timezone info
- Immutable logs stored with WORM (append-only)
- Cryptographic signing of archive blocks (future enhancement)

## 15. Quick Reference

### 15.1 Python Logging Cheat Sheet

```python
import logging
logger = logging.getLogger(__name__)

# DEBUG
logger.debug("Message", extra={"key": value})
# INFO
logger.info("Message", extra={"key": value})
# WARNING
logger.warning("Message", extra={"key": value})
# ERROR
logger.error("Message", extra={"key": value}, exc_info=True)
# CRITICAL
logger.critical("Message", extra={"key": value}, exc_info=True)
```

### 15.2 Span/Context Pattern

```python
# Start span
async with SpanLogger("Operation", param=value) as span:
    # do work
    result = await do_something()
    span.extra["result"] = result

# Automatic End log on __aexit__
```

### 15.3 Structured Logging Pattern

```python
logger.info("BusinessEvent", extra={
    # Always include: event identity, user context, time context
    "event_id": str(uuid.uuid4()),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "user_id": user_id,
    "correlation_id": correlation_id_var.get(),
    # Event-specific context
    "order_id": str(order.id),
    "symbol": symbol,
})
```
