# Logging Standards

## Log Levels Usage

### DEBUG
- Development troubleshooting
- Detailed state information
- Variable values during execution
- SQL queries (in development only)

### INFO
- Normal operational events
- Order placed/cancelled
- Market data received
- Strategy signals generated
- Startup/shutdown events

### WARNING
- Recoverable errors
- Rate limiting approaching
- Cache miss on expected hit
- Deprecated API usage
- Slow external call (>1s)

### ERROR
- Failures requiring attention
- Order execution failures
- Exchange connection lost
- Database errors
- Unhandled exceptions

### CRITICAL
- System-unavailable conditions
- Database unreachable
- Multiple exchange failures
- Data corruption detected

## Structured Logging Format

### JSON Format (Production)
- timestamp: ISO 8601 UTC
- level: DEBUG|INFO|WARNING|ERROR|CRITICAL
- service: Component name
- component: Sub-component
- correlation_id: Request tracking ID
- user_id: User identifier
- message: Human-readable description
- context: Additional structured data
- duration_ms: Operation duration

### Console Format (Development)
- Timestamp | Level | Service:Component | Message | Key=Value pairs

## Contextual Logging

### Correlation IDs
- Generate unique ID per request
- Propagate through all service calls
- Include in all log entries for the request
- Enable distributed tracing

### Component Context
- Log which module/service generated the entry
- Include relevant sub-component name
- Track cross-module operations

### Request Context
- Include request path and method for API calls
- Include user identifier
- Include session context for WebSocket

## What to Log

### Business Events
- Order lifecycle events (created, filled, cancelled)
- Portfolio updates (position opened, closed)
- Risk events (limit reached, exposure changed)
- Strategy events (signal generated, backtest completed)
- Notifications sent

### Technical Events
- External API calls (request, response, status)
- Database operations (query time, rows affected)
- Cache operations (hit/miss, eviction)
- Service startup and shutdown
- Health check results

### Security Events
- Authentication attempts
- API key access
- Configuration changes
- Rate limit enforcement

## What NOT to Log

### Never Log
- API keys, tokens, passwords
- Private keys for exchanges
- JWT tokens or session tokens
- Raw request bodies with sensitive data
- Stack traces in production (use ERROR level with sanitized info)

### Sanitize Before Logging
- Truncate long strings
- Hash sensitive identifiers
- Remove internal IPs from external logs
- Exclude headers with auth tokens

## Log Management

### Retention Policy
- DEBUG: Not persisted in production
- INFO: 30 days
- WARNING: 60 days
- ERROR: 90 days
- CRITICAL: 1 year

### Rotation
- Daily rotation at midnight UTC
- Maximum file size: 100MB
- Compress rotated logs (gzip)
- Delete expired logs automatically

### Storage
- Volume-mounted for persistence
- Optional external log aggregator
- Structured logs for easy parsing
- Indexed by timestamp, level, service

## Distributed Tracing

### Trace Context
- Propagate trace ID across services
- Link logs to traces
- Include span information in context

### Sampling
- 100% for ERROR and CRITICAL
- 10% for INFO and WARNING
- 0% for DEBUG in production
- Configurable per environment

### Correlation with Metrics
- Logs linked to metrics (request count, latency)
- Alert correlation with log events
- Dashboard integration
