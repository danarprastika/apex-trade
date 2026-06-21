# Future Extension Strategy

## Extension Points Design

### Plugin Architecture (Future)
- Define extension interfaces in Domain layer
- Plugins register via configuration
- Plugin discovery via entry points
- Lifecycle hooks for plugins

### Current Extension Strategy
- Module-based: Add new modules without changing core
- Adapter pattern: New exchange adapters, AI providers
- Configuration-driven: Feature flags for new features
- Event-driven: New handlers without modifying existing code

## Adding New Exchange Adapters

### Steps
1. Create new adapter class implementing ExchangeClient interface
2. Add exchange-specific configuration
3. Register adapter in factory
4. Add exchange-specific tests
5. Update documentation

### Required Implementation
- connect(): Establish connection to exchange
- fetch_ticker(): Get current ticker data
- place_order(): Execute order
- cancel_order(): Cancel existing order
- fetch_balance(): Get account balance

### Configuration
- Add to exchanges.enabled list
- Provide API key and secret
- Configure rate limits per exchange

## Adding New Strategy Types

### Strategy Template
1. Create new strategy entity subclass
2. Implement generate_signal() method
3. Add AI prompt template (if AI-driven)
4. Register strategy type in factory
5. Add backtest validation

### Strategy Types (Examples)
- Momentum Strategy: Follows price trends
- Mean Reversion: Trades on price deviations
- Arbitrage: Exploits price differences
- AI-Defined: LLM-generated strategies

### Registration
- STRATEGY_REGISTRY maps strategy names to classes
- New strategies registered at startup
- Configuration selects active strategies

## Adding New AI Model Providers

### Provider Interface
- generate_strategy(): Create trading strategy
- analyze_market(): Analyze market conditions
- health_check(): Verify provider availability

### Steps
1. Implement AIProvider interface
2. Add provider-specific configuration
3. Update fallback chain
4. Add prompt templates
5. Test provider integration

### Fallback Chain Configuration
- primary: gemini
- fallback: openrouter
- timeout: 30 seconds
- providers: gemini, openrouter with?????

## Adding New Notification Channels

### Notification Gateway Interface
- send(): Deliver notification
- health_check(): Verify channel availability

### Supported Channels
- Telegram (implemented)
- Email (future)
- SMS (future)
- WebSocket (future)
- Desktop notifications (future)

### Implementation
1. Implement NotificationGateway interface
2. Add channel-specific configuration
3. Register in notification dispatcher
4. Add template support
5. Test delivery

## Horizontal Scaling Path

### When to Scale
- Multiple exchanges with high data volume
- Sub-second latency requirements
- Multiple concurrent users (future feature)
- High-frequency trading strategies

### How to Scale

#### Step 1: Separate Containers
- Dedicated container per exchange
- Dedicated container for AI processing
- Load balancer in front of API

#### Step 2: Database Scaling
- Read replicas for reporting queries
- Connection pooling with PgBouncer
- Partitioning for market data (by date)

#### Step 3: Cache Scaling
- Redis Cluster for high throughput
- Cache sharding by symbol
- Local caches for hot data

#### Step 4: Message Queue
- Redis Streams or RabbitMQ for event processing
- Decouple producers from consumers
- Enable async processing

### Current Architecture Supports
- Stateless backend (scale horizontally with load balancer)
- Redis for shared state
- PostgreSQL for persistence

## Backward Compatibility Guarantees

### API Compatibility
- Semantic versioning for API
- /api/v1/ endpoints stable for 12 months
- Deprecation warnings in response headers
- Migration guide for breaking changes

### Database Compatibility
- All migrations reversible
- No data loss on rollback
- Additive schema changes preferred
- Deprecated columns marked, not dropped immediately

### Configuration Compatibility
- Old config keys supported with deprecation warning
- New keys additive, not breaking
- Environment variable names stable

## Migration Strategies

### Schema Migrations
1. Add new columns (nullable first)
2. Backfill data in batches
3. Update application code
4. Make new columns non-nullable
5. Remove old columns (after deprecation period)

### Code Migrations
1. Add new interface alongside old
2. Implement new interface
3. Gradual migration of callers
4. Deprecate old interface
5. Remove old interface

### Data Migrations
- Script-based migrations in migrations/ folder
- Run during deployment
- Verify before and after
- Rollback scripts included
