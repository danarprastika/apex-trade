# Architecture Decision Summary

# QuantX AI - Architecture Decision Summary

## Overview

This document summarizes all architectural decisions made for QuantX AI, serving as the single source of truth for the project's technical direction. These decisions were made with consideration for the project's constraints: single-user, single-VPS, production-grade security, and long-term maintainability.

---

## 1. Technology Stack Decisions

### 1.1 Backend

| Component | Choice | Alternatives Considered | Rationale |
|-----------|--------|------------------------|-----------|
| Runtime | **Python 3.12+** | Node.js, Go | Mature async ecosystem, CCXT compatibility, AI library support |
| Web Framework | **FastAPI** | Flask, Django, Aiohttp | Native async, Pydantic v2 integration, auto-generated docs, OpenAPI |
| ORM | **SQLAlchemy 2.x** | Tortoise ORM, Prisma, raw SQL | Mature async support, query building flexibility, ecosystem |
| Migrations | **Alembic** | Flyway, custom scripts | SQLAlchemy native, autogenerate, version control |
| Validation | **Pydantic v2** | Marshmallow, Cerberus | Type safety, FastAPI native, excellent error messages |
| Caching | **Redis** | Memcached | Pub/sub for event architecture, persistence, rich data structures |
| Testing | **pytest** | unittest, nose2 | Fixture ecosystem, parametrization, third-party plugins |
| Telegram | **aiogram 3.x** | python-telegram-bot | Fastest-iterating, async-native, modern Python 3.12+ |
| AI (Primary) | **Gemini API** | OpenAI, Anthropic | Cost-effective, large context window, JSON mode |
| AI (Fallback) | **OpenRouter** | Direct API | Multi-model fallback, unified interface |

### 1.2 Frontend

| Component | Choice | Alternatives Considered | Rationale |
|-----------|--------|------------------------|-----------|
| Framework | **React 18+** | Vue, Svelte, Solid | Largest ecosystem, concurrent features, proven at scale |
| Language | **TypeScript 5+** | JavaScript | Type safety, better refactoring, self-documenting APIs |
| Build Tool | **Vite** | Webpack, Turbopack | Fast HMR, modern Rollup-based builds, plugin ecosystem |
| UI Library | **shadcn/ui + Tailwind** | MUI, Chakra, raw CSS | Fully customizable, copy-paste components, Headless UI |
| Data Fetching | **TanStack Query** | React Query v3, SWR, Zustand | Server-state management, caching, optimistic updates |
| Charts | **Lightweight Charts (TradingView)** | Recharts, D3, Chart.js | Purpose-built for financial data, performance |
| CSS | **TailwindCSS** | CSS Modules, Emotion | Utility-first, purge for bundle size, design tokens |

### 1.3 Infrastructure

| Component | Choice | Alternatives Considered | Rationale |
|-----------|--------|------------------------|-----------|
| Containers | **Docker + Compose** | Kubernetes, Podman | Simple for single VPS, reproducible, fast iteration |
| Proxy | **Nginx** | Caddy, Traefik | Mature, performant, complex config possible |
| CI/CD | **GitHub Actions** | GitLab CI, Jenkins | Native GitHub integration, secrets, matrix, free tier |
| Secrets | **Docker Secrets** (dev), **Vault** (prod) | AWS Secrets Manager, environment files | No secrets in images, RBAC-ready |
| Server | **Linux VPS** | Cloud Run, Lambda, Heroku | Full control, no vendor lock-in, cost-effective |

---

## 2. Architecture Decisions

### ADR-001: Clean Architecture Adoption

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need architecture that enforces dependency rules, enables testing, and supports long-term evolution.

**Decision**: Adopt Clean Architecture with strict layer separation.

**Rationale**:
- Domain purity enables testing without infrastructure
- Clear dependency direction (inward only)
- Dependency Inversion via repository interfaces
- Easy to swap implementations (e.g., PostgreSQL → TimescaleDB)

**Consequences**:
- Additional abstraction layer (interfaces)
- More files to manage
- Steeper learning curve for team
- BUT: Maximum testability, flexibility, and maintainability

### ADR-002: Single-User, Single-Tenant Design

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Project is for ONE USER ONLY. No multi-tenancy required.

**Decision**: Design as single-tenant system. No user/tenant isolation in database or application.

**Rationale**:
- Eliminates authentication complexity (no passwords)
- Simplifies data model (no tenant_id foreign keys)
- Eliminates authorization layer overhead
- Better performance (no joins on tenant_id)
- Fewer attack surface and misconfiguration risks

**Consequences**:
- Cannot evolve to multi-tenant without major refactor
- All data implicitly belongs to single user
- Future multi-tenant would require new bounded context

### ADR-003: Async-First Design

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need to handle many concurrent I/O operations (exchange APIs, AI services, WebSockets).

**Decision**: All I/O in application and domain layers must be async. No blocking calls.

**Rationale**:
- Better throughput for concurrent exchange connections
- Natural fit for async UI frameworks (aiogram, FastAPI + Uvicorn)
- Lower memory footprint per concurrent operation
- Future-ready for async-native operations

**Consequences**:
- All repository interfaces must have async signatures
- Developers must understand async/await patterns
- Debugging async code harder than sync
- All third-party libraries must support asyncio

### ADR-004: Domain Layer Purity

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Domain logic must be testable without infrastructure dependencies.

**Decision**: Domain layer imports ONLY from stdlib and typing. No external framework imports.

**Rationale**:
- Domain tests run without database, network, or services
- Business logic isolated from framework changes
- Dependency Inversion naturally enforced
- Ubiquitous language lives in domain

**Consequences**:
- Cannot use Pydantic models in domain (use plain classes)
- Cannot use SQLAlchemy models in domain
- Use dataclasses/frozen classes for value objects
- Additional mapping code in infrastructure layer

### ADR-005: CCXT for Exchange Integration

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need to support multiple exchanges (Binance, Coinbase, Kraken) with unified API.

**Decision**: Use CCXT library for all exchange connectivity.

**Rationale**:
- Single library for 100+ exchanges
- Built-in normalization of responses
- Handles rate limiting per exchange
- Active maintenance and community
- Supports both REST and WebSocket

**Consequences**:
- Vendor lock-in to CCXT API
- Performance overhead for normalization
- Must handle CCXT-specific errors
- Exchange-specific features may need direct API calls

### ADR-006: Event-Driven Within Bounded Contexts

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need loose coupling between trading, portfolio, and analysis contexts.

**Decision**: Use in-process event bus for inter-context communication.

**Rationale**:
- Decouples publisher from subscriber
- Enables eventual consistency where appropriate
- Simple to implement (no message broker needed initially)
- Extensible to persistent message queue later

**Consequences**:
- Debugging event flow requires tracing
- Risk of over-engineering simple flows
- Must design event contracts carefully

### ADR-007: Redis for Caching and Pub/Sub

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need fast caching for market data and event distribution for WebSocket.

**Decision**: Use Redis for both caching and pub/sub.

**Rationale**:
- Single tool for multiple needs
- Fast in-memory operations
- Pub/sub built-in (no extra infrastructure)
- Persistence option if needed
- Mature client library

**Consequences**:
- Redis failure must be handled gracefully
- Memory limits must be configured
- Cache invalidation strategy required

### ADR-008: Docker Compose for Orchestration

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need repeatable, version-controlled infrastructure for single VPS.

**Decision**: Docker Compose for all service orchestration.

**Rationale**:
- Single command: `docker-compose up`
- Services isolated but connected
- Environment parity (dev/staging/prod)
- Simple for single-server deployment
- Upgrade path to Kubernetes exists

**Consequences**:
- Not suitable for multi-VPS scaling (future: Kubernetes)
- No built-in auto-scaling
- Shared logs require additional setup

### ADR-009: Telegram as Primary User Interface

**Status**: Accepted
**Date**: 2025-06-22

**Context**: User wants chat-based control without browser overhead.

**Decision**: Build Telegram bot as primary interface. Web UI for visualization.

**Rationale**:
- Always-available on phone
- Secure (Telegram identity verification)
- Keyboard interfaces for frequent commands
- Inline alerts and notifications built-in
- Low-friction user experience

**Consequences**:
- Telegram rate limits must be respected
- Rich UI requires Web (can't do complex charts in Telegram)
- API changes from Telegram may break handlers

### ADR-010: Feature Flags for Gradual Rollout

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need safe experimentation without deplloyment gates.

**Decision**: Implement feature flags for incomplete/experimental features.

**Rationale**:
- Decouple deployment from release
- A/B testing capability
- Instant rollback (no code deployment needed)
- Safe experimentation

**Consequences**:
- Flags must be cleaned up
- Adds configuration complexity
- Can become feature flags blob (`if feature_x ... else if feature_y ...`)

### ADR-011: AI Provider Failover Strategy

**Status**: Accepted
**Date**: 2025-06-22

**Context**: AI is critical for analysis. Single provider creates single point of failure.

**Decision**: Primary (Gemini) + Fallback (OpenRouter) with circuit breaker.

**Rationale**:
- Cost optimization (use cheaper primary, fallback on failure)
- High availability
- Vendor diversification
- Graceful degradation

**Consequences**:
- Response format normalization between providers
- Cost tracking per provider
- Failover logic in AI router must be tested
- Latency overhead for dual-provider

### ADR-012: Standard Error Format Across All Layers

**Status**: Accepted
**Date**: 2025-06-22

**Context**: Need consistent error handling from domain to presentation.

**Decision**: Typed exception hierarchy with structured error data.

**Rationale**:
- Consistent API responses
- Easier error handling in client code
- Clear traceability from UI to domain
- Supports both REST and Telegram (different response formats)

**Consequences**:
- More verbose error handling code
- Must map domain errors to HTTP status codes
- Must map domain errors to Telegram messages

---

## 3. Rejected Alternatives

| Decision | Rejected Because |
|----------|----------------|
| Django over FastAPI | Too monolithic, poor async support, heavier than needed |
| Flask over FastAPI | No async support, fewer batteries included, manual validation |
| Prisma ORM | PostgreSQL-specific features, less flexible queries |
| MongoDB over PostgreSQL | No ACID guaranteed, weaker query capabilities for financial data |
| GraphQL | Overkill for single-user, simpler REST works fine |
| Microservices | Increased operational complexity, not needed for single-user scale |
| Kubernetes | Overkill for single VPS, complexity far exceeds benefit |
| Celery/Redis Queue | Background jobs rare enough for in-memory queue |
| TypeORM over SQLAlchemy | Less mature async, smaller ecosystem |
| Next.js over Vite+React | Overkill for read-only views, heavier deployment |
| D3.js over TradingView Charts | Too low-level, financial charts have many requirements |
| self-hosted LLM (Llama) | Compute cost prohibitive, latency high, quality lower |

---

## 4. Key Trade-offs Accepted

### 4.1 Flexibility vs. Complexity

| Trade-off | Decision | Trade-off Made |
|-----------|----------|----------------|
| Multi-exchange | Accept | More adapters needed, CCXT abstracts complexity |
| Async-only | Accept | Easier testing becomes harder (async fixtures) |
| Strict layering | Accept | More boilerplate (interfaces) for better testability |
| Full TypeScript | Accept | More compile time, better IDE support |

### 4.2 Security vs. Usability

| Trade-off | Decision | Trade-off Made |
|-----------|----------|----------------|
| No auto-login for security | Accept | Must authenticate via Telegram (one-time) |
| No dark patterns | Accept | Clean UI always, even if slower conversion |
| Strict input validation | Accept | Reject rather than coerce malformed data |

### 4.3 Development Speed vs. Maintainability

| Trade-off | Decision | Trade-off Made |
|-----------|----------|----------------|
| Full architecture | Accept | More upfront cost, lower long-term cost |
| Comprehensive tests | Accept | Slower initial development, fewer production bugs |
| Documentation-first | Accept | Documentation required before implementation |

---

## 5. Validation Criteria

The architecture is validated when:
1. All 20 documentation files complete ✓
2. CI pipeline passes on first commit ✓
3. First component (Hello World) deploys to VPS ✓
4. First test (placeholder) passes ✓
5. No import-linter violations in base structure ✓

---

## 6. Future Review Triggers

Revise these decisions when:
- Team size > 3 (revisit microservices)
- Requests per second > 1000 (revisit CQRS/sharding)
- Data volume > 1TB (revisit partitioning)
- Users > 100 (revisit multi-tenancy)
- Budget > $1000/month (revisit self-hosted vs cloud)

---

## 7. Architecture Governance

### 7.1 Who Can Change Architecture
- CTO / Principal Architect (primary)
- Senior engineer with CTO approval
- Changes require at least 24-hour review period

### 7.2 Change Process
1. Propose change via ADR document
2. Present rationale and alternatives
3. Review phase: feedback and iteration
4. Approval or rejection with reasoning
5. If approved: update documentation, schedule migration

### 7.3 Exception Process
For emergency changes (production bugs):
1. Apply hotfix with minimal scope
2. Document exception via ADR after fix
3. Review exception within 48 hours
4. Determine if permanent change needed

---

## Appendix: Decision Matrix

| Area | Decision | Reversible? | Confidence |
|------|----------|-------------|------------|
| Python + FastAPI | No | Medium | High |
| Clean Architecture | Difficult | Low | High |
| PostgreSQL + Redis | No | Low | High |
| CCXT | Yes | High | High |
| aiogram 3.x | Yes | High | High |
| Docker Compose | Yes | High | High |
| Single-User design | No | Low | High |
| Async-First | Difficult | Low | High |
| Domain Purity | Difficult | Low | High |
| Event-Driven | Yes | High | Medium |
| Feature Flags | Yes | High | Medium |
| AI Failover | Yes | High | High |

**Confidence Level Legend**:
- **High**: Strong evidence, widely adopted pattern
- **Medium**: Good reasoning, some uncertainty
- **Low**: Experimental, requires validation
