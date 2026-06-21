# Architecture Decision Summary

## Key Architecture Decision Records (ADRs)

### ADR-001: Clean Architecture

**Status**: Accepted  
**Date**: 2024-01-01

**Context**
Need an architecture that separates business logic from frameworks, enables testing, and supports long-term maintainability for a personal trading system.

**Decision**
Adopt Clean Architecture with four layers: Domain, Application, Infrastructure, Presentation.

**Rationale**
- Testability without external dependencies (database, APIs)
- Framework independence (can swap FastAPI, React, etc.)
- Clear separation of concerns
- Business logic remains stable as infrastructure evolves
- Well-documented patterns, industry-proven

**Alternatives Considered**
- Traditional layered architecture: Simpler but weaker boundaries
- Hexagonal architecture: Similar benefits, different naming
- Microservices: Overkill for single-user system

**Trade-offs**
- More files and indirection for simple features
- Learning curve for team (single developer)
- Initial setup time longer

### ADR-002: Domain-Driven Design

**Status**: Accepted  
**Date**: 2024-01-01

**Context**
Trading domain has complex business rules (position limits, risk constraints, order lifecycle). Need explicit modeling to avoid bugs.

**Decision**
Apply DDD tactical patterns: Entities, Value Objects, Aggregates, Domain Services, Repositories, Domain Events.

**Rationale**
- Complex trading rules need explicit representation
- Value objects prevent invalid states (e.g., negative prices)
- Domain events enable decoupled communication
- Bounded contexts organize complexity
- Facilitates future multi-user extension

**Alternatives Considered**
- Anemic domain model (entities with only data): Simpler but loses business logic encapsulation
- Procedural approach: Faster to write, harder to maintain

**Trade-offs**
- More upfront design work
- More classes for simple operations
- Discipline required to maintain purity

### ADR-003: FastAPI over Django

**Status**: Accepted  
**Date**: 2024-01-01

**Context**
Need web framework for API backend. Considering FastAPI, Django, Flask.

**Decision**
Use FastAPI.

**Rationale**
- Async-first design matches requirements (many I/O operations)
- Lightweight, minimal overhead
- Native OpenAPI documentation
- Pydantic integration for validation
- Type hints throughout
- High performance (comparable to NodeJS)

**Alternatives Considered**
- Django: Batteries included but heavier, less async-native
- Flask: Too minimal, no built-in async, validation
- FastAPI with Django ORM: Best of both, but complexity

**Trade-offs**
- Less batteries included than Django
- Smaller ecosystem
- Need to choose own libraries for everything

### ADR-004: PostgreSQL over MongoDB

**Status**: Accepted  
**Date**: 2024-01-01

**Context**
Need database for trading data. Financial data requires ACID transactions.

**Decision**
Use PostgreSQL with TimescaleDB extension (future).

**Rationale**
- ACID transactions critical for financial data
- Relational model fits portfolio/order/position relationships
- Mature, reliable, battle-tested
- JSON support for flexible data
- TimescaleDB for time-series market data
- Rich query capabilities for analytics

**Alternatives Considered**
- MongoDB: Flexible but eventual consistency, weaker transactions
- MySQL: Similar to PostgreSQL, less feature-rich
- InfluxDB: Good for time-series, poor for relational data

**Trade-offs**
- Schema migrations required
- Less flexible for schema changes
- Horizontal scaling more complex

### ADR-005: CCXT for Exchange Integration

**Status**: Accepted  
**Date**: 2024-01-01

**Context**
Need to integrate multiple cryptocurrency exchanges. Each has different API.

**Decision**
Use CCXT library for exchange integration.

**Rationale**
- Unified interface for 100+ exchanges
- Supports REST and WebSocket
- Well-maintained, active community
- Handles rate limiting, retries, normalization
- Python-native

**Alternatives Considered**
- Direct API integration: More work, harder to maintain
- Custom abstraction: Reinventing the wheel

**Trade-offs**
- Additional dependency
- Abstraction leak possible (exchange-specific features)
- Library bloat (many unused exchanges)

### ADR-006: Gemini API as Primary AI Provider

**Status**: Accepted  
**Date**: 2024-01-01

**Context**
Need LLM for strategy generation and market analysis.

**Decision**
Use Gemini API as primary, OpenRouter as fallback.

**Rationale**
- Good performance for financial analysis
- Competitive pricing
- Clean API design
- OpenRouter provides access to multiple models

**Alternatives Considered**
- OpenAI only: Good but more expensive
- Self-hosted LLM: Complex, requires GPU
- Local LLM: Insufficient quality for trading decisions

**Trade-offs**
- API dependency for AI features
- Cost per API call
- Latency for remote API calls

## Principles Established

### Async First
All I/O operations are async. Database, HTTP, file system access use async patterns.

### Security First
Input validation, secrets management, encryption, audit logging are non-negotiable.

### Testability
Everything testable via dependency injection. No hidden dependencies.

### Observability
Structured logging, health checks, metrics on all components.

### Deployability
Docker, health checks, rollback procedures, zero-downtime deployment.

## Known Limitations

### Current Limitations
- Single instance deployment: No true high availability
- Manual secret management: No vault integration
- Limited to crypto exchanges: No stocks, forex
- Single-user only: By design, not a limitation
- No mobile app: Web dashboard only

### Future Reconsideration Points
- When trading volume exceeds single VPS capacity
- When multi-user access is needed
- When regulatory requirements change
- When AI costs become significant
- When exchange API limits are hit

## Trade-offs Summary

| Decision | Trade-off |
|----------|-----------|
| Clean Architecture | More files/indirection vs simpler structure |
| DDD | More classes vs anemic model |
| Async everywhere | Complexity vs performance |
| PostgreSQL | Schema rigidity vs data consistency |
| Single VPS | Simplicity vs high availability |
| Personal system | No multi-tenant overhead vs limited market |
