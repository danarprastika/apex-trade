# Architecture Decision Summary

## 1. Core Architectural Decisions

| Decision | Options Considered | Decision | Rationale |
|----------|-------------------|----------|-----------|
| **Monolith vs Microservices** | Microservices, Monolith, Modular Monolith | Modular Monolith (Clean Arch) | Single-user, single VPS, simplicity without sacrificing domain clarity. Migrate to microservices only when scaling demands it. |
| **Backend Framework** | Flask, Django, FastAPI, Aiohttp | FastAPI | Native async, Pydantic integration, auto-generated OpenAPI docs, type safety, modern Python 3.12+ first-class support. |
| **Database** | MongoDB, PostgreSQL, MySQL | PostgreSQL | ACID compliance for financial data, rich query capabilities, JSON support (hybrid), proven scalability, extensive ORM support. |
| **Cache** | Redis, Memcached, In-memory | Redis | Pub/sub for event-driven architecture, persistence option, rich data structures, flexible TTL. |
| **ORM** | SQLAlchemy 2.x, Tortoise ORM, raw SQL | SQLAlchemy 2.x | Industry standard, excellent async support, Alembic native, mature ecosystem, type safety with modern Python. |
| **Migration Tool** | Alembic, Flyway, custom scripts | Alembic | SQLAlchemy native, widely supported, reliable, model-driven migrations. |
| **Validation** | Manual validation, Marshmallow, Pydantic, Cerberus | Pydantic v2 | Native FastAPI integration, excellent performance, type coercion, clear error messages, async validation support. |
| **Exchange Library** | ccxt, exchange-specific REST APIs, websockets | CCXT | Unified API for 100+ exchanges, battle-tested, handles normalization, rate limiting built-in. |
| **Telegram Library** | python-telegram-bot, aiogram, Telethon | aiogram 3.x | Native async/await, modern Python 3.12+ support, fast, high-level API for handlers and middlewares. |
| **Frontend Framework** | React, Vue, Svelte, vanilla JS | React | Largest ecosystem, TypeScript support, mature community, TanStack Query integration, proven at scale. |
| **UI Library** | MUI, Chakra UI, shadcn/ui, Headless UI | shadcn/ui (Tailwind) | Fully customizable, copy-paste approach, no lock-in, Tailwind composition, excellent TypeScript support. |
| **Data Fetching** | React Query, SWR, Redux, Zustand, Apollo | TanStack Query | Server-state management, caching, background refetching, optimistic updates, TypeScript-first. |
| **CSS Framework** | CSS Modules, Styled Components, Tailwind, Emotion | TailwindCSS | Utility-first, production-ready design system (shadcn), rapid development, purge for optimal bundle size. |
| **Build Tool** | Webpack, Vite, Parcel, esbuild | Vite | Fast HMR, modern Rollup-based production builds, plugin ecosystem, TypeScript out of box. |
| **CI/CD** | GitHub Actions, GitLab CI, Jenkins, CircleCI | GitHub Actions | Native GitHub integration, generous free tier, ecosystem marketplace, matrix builds, secrets management. |
| **Container Orchestration** | Docker Compose, Kubernetes, Swarm | Docker Compose | Single VPS deployment, simplicity, fast iterations, sufficient for single-user scale. Upgrade path to K8s ready. |
| **Web Server** | Nginx, Caddy, Traefik | Nginx | Mature, performant, flexible SSL via Let's Encrypt, extensive documentation, battle-tested for production. |
| **AI Provider (Primary)** | OpenAI GPT-4, Anthropic Claude, Google Gemini, Cohere | Gemini API | Low-cost API access, high throughput, structured output, JSON mode, 2M token context for deep analysis. |
| **AI Provider (Fallback)** | OpenRouter (multi-model) | OpenRouter | Unified API routing to multiple LLM providers, fallback capability if primary fails. |

## 2. Architecture Style Decision

### 2.1 Choice: Clean Architecture (Hexagonal)

| Style | Rationale for Rejection |
|-------|-------------------------|
| Clean Arch + DDD | ✅ Chosen - Enforces domain purity, testability, maintainability. |
| Layered (Traditional) | ❌ Dependencies flow wrong direction; easy to violate layer boundaries. |
| Microservices | ❌ Overkill for single user; adds operational complexity, CI/CD, distributed tracing overhead. |
| Event-Driven (Full) | ❌ Adds complexity for non-critical async requirements; use selectively within monolith. |
| Hexagonal (Ports & Adapters) | ✅ Same principles as Clean Arch; terminology different, same architecture. |

### 2.2 Layered Architecture Enforcement

```yaml
layer_0: Domain (Core)
  - Allowed: stdlib, typing, __future__
  - Forbidden: Any external library import
  - Dependencies: None outward

layer_1: Application (Use Cases)
  - Allowed: Layer 0 + external utilities (tenacity, pydantic)
  - Forbidden: Layer 2 (Infrastructure), Layer 3 (Presentation)
  - Dependencies: Module 0 inward

layer_2: Infrastructure (Implementations)
  - Allowed: Layer 0 + Layer 1 + external libraries (SQLAlchemy, aiohttp, ccxt)
  - Forbidden: Layer 3 (Presentation)
  - Dependencies: Module 0 + 1 inward

layer_3: Presentation (UI / API)
  - Allowed: Layer 1 + Layer 2 (DI only) + external libraries (FastAPI, aiogram)
  - Forbidden: None outward
  - Dependencies: Module 0 + 1 + 2 inward
```

**Enforcement**:
- CI check with `import-linter` or custom script
- Pre-commit hook with `ruff` or custom linter
- Build failures on violations

## 3. Technology Stack Justification

### 3.1 Backend
| Component | Choice | Why |
|-----------|--------|-----|
| Runtime | Python 3.12+ | Best async support, CCXT compatibility, AI SDKs |
| Web Framework | FastAPI | Modern, async, OpenAPI docs auto-gen, type hints |
| ORM | SQLAlchemy 2.x | Mature, great async, queries composable |
| Migrations | Alembic | SQLAlchemy ecosystem, version control |
| Validation | Pydantic v2 | Performance, type safety, FastAPI native |
| Caching | Redis | Pub/sub, persistence, structures |
| Testing | pytest | De-facto standard, fixtures, plugins |
| Lint/Format | ruff | Rust-based, fast, replaces multiple tools |

### 3.2 Frontend
| Component | Choice | Why |
|-----------|--------|-----|
| Framework | React 18+ | Mature, huge ecosystem, concurrent features |
| Language | TypeScript | Type safety, better DX, fewer runtime bugs |
| Build Tool | Vite | Fast, modern, Rollup production builds |
| UI Library | shadcn/ui | Copy-paste Radix + Tailwind, full customization |
| Data Fetching | TanStack Query | Optimistic updates, caching, background refetch |
| Charts | TradingView Lightweight | Canvas-based, optimized for financial data |
| CSS | TailwindCSS | Utility-first, minimal runtime, purge for bundle |

### 3.3 Infrastructure
| Component | Choice | Why |
|-----------|--------|-----|
| Containers | Docker + Compose | Reproducible, portable, development/prod parity |
| Reverse Proxy | Nginx | Mature, performant, SSL termination |
| Deployment | GitHub Actions | Native GitHub, secrets, matrix, cached |
| Secrets | Docker Secrets (local), Vault (future) | No secrets in images or env files |

## 4. Key Design Decisions

### 4.1 Single-User Constraint
**Decision**: Enforce single-user (one portfolio, no multi-tenancy).
**Rationale**: Eliminates tenant isolation overhead, simplifies data model, allows simpler authorization.

**Implementation**:
```python
class Portfolio:
    @property
    def user_id(self) -> UUID:
        """Single user - no tenant isolation needed."""
        return SINGLE_USER_ID
```

### 4.2 Async-First Design
**Decision**: All I/O is async by default.
**Rationale**: Better throughput for concurrent operations (market data streaming, multiple exchange connections, AI calls).

**Alternatives Considered**:
- Sync: Simpler but bad for concurrent market data
- Hybrid (FastAPI sync controllers): Adds complexity

### 4.3 Repository Pattern + UnitOfWork
**Decision**: All data access through repository interfaces.
**Rationale**: Decouples domain from database implementation, enables testing with mocks, swap persistence without changing business logic.

**Benefits**:
- Testability: Swap for in-memory or mock repos
- Flexibility: Swap PostgreSQL for TimeScaleDB (future)
- Clarity: Repository contracts document data access patterns

### 4.4 CQRS Light
**Decision**: Use Command/Query separation for Use Cases (not full CQRS).
**Rationale**: Separates read/write concern at use case level without overhead of separate models, migrations. Use separate entities for read models only if performance demands.

**Implementation**:
```
application/use_cases/commands/  # Writes (place_order, cancel_order)
application/use_cases/queries/   # Reads (get_portfolio, get_history)
```

### 4.5 AI Provider Abstraction
**Decision**: AIPRouter with failover + circuit breaker.
**Rationale**: Avoid vendor lock-in, ensure availability, manage costs.

```python
class AIService:
    def __init__(
        self,
        primary: AIProvider  # Gemini
        fallback: AIProvider,  # OpenRouter
    ):
        ...
```

## 5. Technology Constraints

| Constraint | Reason | Mitigation |
|------------|--------|------------|
| Python 3.12+ | Async improvements, performance | Pin minimum version in pyproject.toml |
| FastAPI >= 0.100 | Pydantic v2 compatibility | Pin major.minor.0 |
| PostgreSQL >= 14 | JSONPath, performance | Use Docker official image |
| Redis >= 7.0 | Performance, modules ecosystem | Pin in compose file |
| React >= 18 | Concurrent features, Suspense | Pin peerDependencies |
| TypeScript >= 5.0 | Modern features, strict mode | Configure tsconfig |

## 6. Non-Negotiable Principles

### 6.1 Domain Purity
Domain layer MUST NOT import from:
- sqlalchemy, asyncpg
- fastapi, pydantic (use plain classes)
- aiohttp, httpx
- ccxt, aiogram

**Allowed**: stdlib, typing, __future__

### 6.2 Secrecy by Default
- `.env` in `.gitignore`
- Logs exclude secrets
- Error messages sanitized
- Database connections encrypted in transit

### 6.3 Single Source of Truth
Architecture documentation is the definitive source for:
- Layer rules
- Naming conventions
- Module structure
- Dependency rules

Code must align with docs. Iterative refinement of docs is OK, but code shouldn't violate documented rules without updating docs.

### 6.4 Observability Built-In
Every component observable:
- Structured logging at INFO+
- Correlation IDs
- Health checks
- Metrics for key operations
- Trace context propagation (future)

## 7. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Python GIL limits concurrency | Use async I/O heavily; CPU-bound tasks offloaded or batched |
| AI API cost overruns | Caching + rate limiting; fallback to OpenRouter free tier |
| Exchange API rate limits | Per-exchange rate limiter; queue with backpressure |
| Database grows unbounded | Time-series partitioning; archival policy |
| Redis memory pressure | LRU eviction; TTL on all keys; size limits |
| Docker Compose limits | Ready to migrate to Kubernetes if VPS scale needed |

## 8. Traceability Matrix

### 8.1 ADR ↔ Sprint ↔ Code Structure

| ADR | Decision | Sprint | Implementation Location | Verification |
|------|----------|--------|------------------------|--------------|
| ADR-001 | Clean Architecture | 0 | docs/architecture/layer-architecture.md | Import-linter in CI |
| ADR-002 | SQLAlchemy + Alembic | 1 | src/infrastructure/database/ | Migration tests |
| ADR-003 | FastAPI + aiogram | 2 | src/presentation/ | Health checks |
| ADR-004 | Single-User Design | 3 | src/domain/ | Integration tests |
| ADR-005 | CCXT + AsyncIO | 4 | src/infrastructure/exchanges/ | Exchange tests |
| ADR-006 | AI Router Pattern | 5 | src/infrastructure/ai/ | Failover tests |
| ADR-007 | Redis Cache | 6 | src/infrastructure/cache/ | Cache hit rate |
| ADR-008 | Docker Compose | 7 | docker-compose.yml | Rebuild tests |

### 8.2 Sprint ↔ DoD ↔ Architecture Principles

| Sprint | Primary DoD | Architecture Principle | Verification |
|--------|-------------|------------------------|--------------|
| 0 | Project initialized | Clean Arch | Layer separation in code |
| 1 | Database operational | DDD | Entity tests |
| 2 | Domain models implemented | SOLID | Test coverage |
| 3 | API operational | Single-User | Portfolio tests |
| 4 | Telegram working | Clean Arch | Handler separation |
| 5 | Orders execution | Repository Pattern | Transaction rollback tests |
| 6 | AI signals | Dependency Injection | Mock injection tests |
| 7 | Production ready | Security First | Security scan pass |
- [ ] User can place/cancel orders via Telegram
- [ ] Trade records generated on fills
- [ ] Positions tracked and updated
- [ ] Notifications sent on events

**Outcomes**:
- Full order lifecycle operational
- Real-time trade and position tracking
- User feedback via Telegram

### 6.6: Web Dashboard

**Goal**: Real-time monitoring and analytics web interface.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| React + Vite setup | P0 | Frontend | 1d | Dev server running |
| TailwindCSS config | P0 | Frontend | 0.5d | Styling framework setup |
| TanStack Query setup | P0 | Frontend | 0.5d | Data fetching + caching |
| Dashboard shell layout | P0 | Frontend | 1d | Responsive layout |
| WebSocket client hook | P0 | Frontend | 1d | Real-time data |
| Portfolio widget | P0 | Frontend | 2d | Real-time balance display |
| Trade history table | P0 | Frontend | 2d | Pagination, sorting |
| Order status widget | P0 | Frontend | 1.5d | Open orders display |
| Auth screen (Telegram) | P1 | Frontend | 1d | JWT-based auth |
| Error handling | P1 | Frontend | 1d | Error boundaries, toasts |
| Accessibility (a11y) | P2 | Frontend | 2d | Screen reader compatible |

**Outcomes**:
- Web UI renders live data via WebSocket
- Charts display price history
- Authentication flow works
- Mobile-responsive

### 6.7: Observability & Alerting

**Goal**: Production operational readiness.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Prometheus metrics | P0 | DevOps | 2d | Export relevant metrics |
| Alert rules | P0 | DevOps | 1d | Telegram + email alerts |
| Log aggregation | P1 | DevOps | 2d | Loki/Grafana Loki |
| Grafana dashboards | P1 | DevOps | 2d | System + trading dashboards |
| Alert routing | P0 | DevOps | 0.5d | On-call notifications |

**Outcomes**:
- System health visible
- Incident response automated
- Root cause analysis facilitated

### 6.8: Security Hardening

**Goal**: Production-grade security posture.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Security audit | P0 | Security | 2d | OWASP Top 10 review |
| Dependency update | P0 | All | 1d | No critical vulnerabilities |
| Penetration testing | P1 | Security | 2d | No critical/high findings |
| Rate limiting | P0 | Backend | 1d | Per endpoint |
| Input validation | P0 | Backend | 1d | Strict Pydantic |
| Secret scanning | P0 | DevOps | 1d | GitGuardian or truffleHog |
| RBAC (future-ready) | P2 | Backend | 1d | Authorization framework |
| Audit logging | P0 | Backend | 1d | Immutable log storage |

**Outcomes**:
- Security audit passed
- Penetration test no critical findings
- Zero-critical CVEs in dependencies

### 6.9: Polish & Beta Launch

**Goal**: Beta release with critical features stabilized.

| Task | Priority | Owner | Est. | Definition of Done |
|------|----------|-------|------|--------------------|
| Comprehensive backup | P0 | DevOps | 2d | Automated backup tested |
| Disaster recovery runbook | P0 | DevOps | 1d | Tested recovery procedure |
| User acceptance testing | P0 | All | 3d | Smoke tests, demo |
| Bug bash | P0 | All | 2d | Critical bugs fixed |
| Rollback process | P0 | DevOps | 1d | One-command rollback tested |
| Beta release | P0 | All | 0.5d | Deployed, documented |

**Outcomes**:
- Beta version deployed and stable
- Backup/recovery tested end-to-end
- Critical bugs resolved

## 6. Sprint Ceremonies

| Ceremony | Duration | Frequency | Purpose |
|----------|----------|-----------|---------|
| Sprint Planning | 4 hours | Start of sprint | Scope selection, task breakdown |
| Daily Standup | 15 minutes | Daily | Blockers, progress sync |
| Demo | 1 hour | End of sprint | Feature demonstration |
| Retrospective | 1 hour | End of sprint | Process improvement |
| Backlog Refinement | 1 hour | Mid-sprint | Prepare next sprint stories |

## 7. Milestone Tracking

| Milestone | Target Date | Deliverable | Success Criteria |
|-----------|-------------|-------------|------------------|
| M0: Infrastructure Ready | End Sprint 1 | Docker services | `docker-compose up` works |
| M1: First Trade | End Sprint 5 | Order via Telegram | User clicks /buy, order placed on Binance testnet |
| M2: AI Analysis Live | End Sprint 6 | Gemini responds | /analyze returns structured analysis |
| M3: MVP Complete | End Sprint 7 | Full MVP | Alpha testers can trade via Telegram |
| M4: Web Dashboard Live | End Sprint 10 | Web UI | Portfolio visible in browser |
| M5: Beta Release | End Sprint 12 | Public beta | Live testing with real capital limits |

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| AI API pricing changes | Low | Medium | Fallback provider, caching | Backend |
| CCXT breaking changes | Medium | High | Pin versions, test on update | Backend |
| Telegram bot ban | Low | High | Follow ToS, rate limiting | Ops |
| Asset price volatility | High | High | Risk limits, circuit breakers | Domain |
| PostgreSQL performance | Low | Medium | Partitioning, indexing | DevOps |
| Team burnout | Medium | High | Sustainable pace, automation | PM |

## 9. Acceleration Strategies

### 9.1 Parallel Work Streams
Sprints with independent scope can run in parallel:

```
Sprint 2 (Domain)    ─┐
                       ├─→ Merge to main together
Sprint 3 (API)        ─┘

Sprint 4 (Telegram)  ──→ Standalone
```

### 9.2 Spike Tasks
Allocate 1 day per sprint for technical spikes:
- Spike: Evaluate new library or approach
- Spike: Performance benchmark
- Spike: Security scan

## 10. Retrospective Enhancements

Each sprint retrospective produces:
- **What went well**: Continue these practices
- **What went poorly**: Address in next sprint
- **Action items**: Specific, measurable changes
- **Learning**: Document and share knowledge