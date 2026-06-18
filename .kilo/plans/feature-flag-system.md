# Feature Flag System Plan for APEX

Version: 0.1  
Status: Draft  
Owner: Infrastructure / Backend  
Scope: Design and implementation roadmap only

---

# 1. Architecture

## 1.1 Current Architecture Context

APEX is designed as a modular monolith first and microservices-ready system.

Current relevant components:

- FastAPI backend
- PostgreSQL database
- Redis cache
- Web dashboard
- Telegram bot
- Market Engine
- Trading Engine
- Risk Engine
- AI Engine
- Monitoring Engine
- Paper trading service
- Live execution service
- Audit logging

Relevant current implementation points:

- Paper trading is already supported through `PaperTradingService`.
- Live trading is handled through `ExecutionService`.
- Users have roles: `VIEWER`, `TRADER`, `ADMIN`, and `SUPER_ADMIN`.
- `UserSettings` already exists and can later support user-level preferences.
- `AuditLog` can record flag changes and enforcement decisions.
- AI governance already defines agent permissions, boundaries, approval workflow, audit, monitoring, and security controls.
- News and Sentiment Intelligence are planned future capabilities.

## 1.2 Target Feature Flag Architecture

The feature flag system should be a first-class backend capability with four layers:

1. API Layer
2. Application Service Layer
3. Domain Model Layer
4. Infrastructure Layer

## 1.3 Core Components

| Component | Responsibility |
|---|---|
| FeatureFlag | Domain entity representing a flag definition and runtime state. |
| FeatureFlagVariant | Optional variant metadata for rollout, segmentation, or experiment configuration. |
| FeatureFlagAssignment | Optional user, role, environment, or segment assignment. |
| FeatureFlagAuditLog | Audit trail for flag creation, updates, enable/disable actions, and overrides. |
| FeatureFlagService | Central service for evaluating flags and applying business rules. |
| FeatureFlagRepository | PostgreSQL persistence for flag definitions, assignments, and audit history. |
| FeatureFlagCache | Redis-backed cache for low-latency flag evaluation. |
| FeatureFlag API | REST endpoints for admin management and client evaluation. |
| Enforcement Points | Trading, AI, news, sentiment, and experimental modules checking flags before execution. |

## 1.4 Required Flags

| Flag Key | Name | Default | Primary Enforcement Point | Notes |
|---|---|---|---|---|
| `paper_trading.enabled` | Paper Trading | `true` | Trading API, paper order endpoint | Allows safe simulation mode. |
| `live_trading.enabled` | Live Trading | `false` | Live order endpoint, execution service | Must behave as a kill switch. |
| `ai_agents.enabled` | AI Agents | `false` | AI agent orchestration, AI endpoints | Must align with AI governance controls. |
| `news_analysis.enabled` | News Analysis | `false` | News collector, news analyzer, news API | Stage 2 feature gate. |
| `sentiment_analysis.enabled` | Sentiment Analysis | `false` | Sentiment collector, sentiment analyzer, sentiment API | Stage 2 feature gate. |
| `experimental_features.enabled` | Experimental Features | `false` | UI, API, experimental modules | Global gate for unstable features. |

## 1.5 Evaluation Model

The system should support:

- Global flag state
- Environment-scoped flag state
- Role-scoped access
- Optional user-scoped override
- Optional percentage rollout
- Optional time window
- Optional dependency on another flag
- Explicit disabled state that overrides all other rules
- Audit logging for administrative changes

## 1.6 Recommended Evaluation Flow

1. Client or service requests flag evaluation.
2. `FeatureFlagService` checks Redis cache first.
3. If cache miss or stale, service loads flag definition from PostgreSQL.
4. Service evaluates global, environment, role, user, rollout, and dependency rules.
5. Service records evaluation metadata if required for audit or high-risk actions.
6. Result is returned to caller.
7. Redis cache is updated with short TTL.
8. Enforcement point allows or blocks the requested feature.

## 1.7 Enforcement Points

| Area | Enforcement Behavior |
|---|---|
| Paper Trading | Require `paper_trading.enabled` before paper-order creation. |
| Live Trading | Require `live_trading.enabled` before real order creation. If disabled, block all live orders. |
| AI Agents | Require `ai_agents.enabled` before agent orchestration, agent decisions, and AI-driven actions. |
| News Analysis | Require `news_analysis.enabled` before news collection, classification, scoring, and news API responses. |
| Sentiment Analysis | Require `sentiment_analysis.enabled` before sentiment collection, scoring, and sentiment API responses. |
| Experimental Features | Require `experimental_features.enabled` before exposing unstable UI, API, or workflow features. |

---

# 2. Storage Strategy

## 2.1 PostgreSQL as Source of Truth

PostgreSQL should store durable flag definitions and history.

Recommended tables:

| Table | Purpose |
|---|---|
| `feature_flags` | Stores flag key, name, description, enabled state, environment, owner, metadata, and timestamps. |
| `feature_flag_assignments` | Stores optional role, user, segment, rollout, or experiment assignment rules. |
| `feature_flag_audit_logs` | Stores administrative changes, old/new values, actor, IP address, and reason. |
| `feature_flag_evaluations` | Optional high-volume evaluation log for audit-heavy or regulated actions. |

## 2.2 Redis as Evaluation Cache

Redis should store evaluated or normalized flag state for low-latency access.

Recommended cache keys:

- Global flags
- Environment-scoped flags
- Role-scoped flags
- User-scoped overrides
- Flag dependency graph
- Flag version or revision marker

Recommended TTL:

- Global flags: short TTL, such as 30 to 120 seconds.
- High-risk flags: shorter TTL, such as 5 to 30 seconds.
- User overrides: short TTL, such as 60 to 300 seconds.

## 2.3 Cache Invalidation Strategy

Cache invalidation should occur when:

- A flag is created.
- A flag is updated.
- A flag is enabled or disabled.
- A flag assignment is changed.
- A dependency flag changes.
- An environment-level override changes.
- A kill switch flag changes.

Invalidation options:

1. Delete specific Redis keys after each change.
2. Increment a global feature flag revision number.
3. Use Redis pub/sub to notify backend instances to clear local cache.

## 2.4 Audit Logging

Audit logging should be mandatory for:

- Flag creation
- Flag update
- Flag enable
- Flag disable
- Environment override changes
- Role override changes
- User override changes
- Rollout percentage changes
- Dependency changes
- Kill switch changes

Audit fields should include:

- Actor user ID
- Actor role
- IP address
- Flag key
- Old value
- New value
- Environment
- Reason
- Created timestamp

## 2.5 Data Retention

Recommended retention:

| Data Type | Retention |
|---|---|
| Flag definition history | 1 year minimum |
| Administrative audit logs | 2 years minimum |
| High-risk evaluation logs | 90 to 365 days depending on compliance needs |
| Redis cache | TTL-based only |

---

# 3. API Requirements

## 3.1 Admin Management API

The backend should expose admin-only endpoints for flag management.

Required endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/admin/feature-flags` | List feature flags with filters for key, enabled state, environment, and owner. |
| GET | `/api/v1/admin/feature-flags/{key}` | Get one feature flag definition and current evaluation rules. |
| POST | `/api/v1/admin/feature-flags` | Create a new feature flag. |
| PUT | `/api/v1/admin/feature-flags/{key}` | Update flag metadata, rules, rollout, and environment scope. |
| PATCH | `/api/v1/admin/feature-flags/{key}/enable` | Enable a flag. |
| PATCH | `/api/v1/admin/feature-flags/{key}/disable` | Disable a flag. |
| GET | `/api/v1/admin/feature-flags/{key}/history` | Get audit history for a flag. |
| POST | `/api/v1/admin/feature-flags/{key}/assignments` | Create role, user, segment, or rollout assignment. |
| DELETE | `/api/v1/admin/feature-flags/{key}/assignments/{assignment_id}` | Remove an assignment. |

## 3.2 Evaluation API

The backend should expose evaluation endpoints for clients and internal services.

Required endpoints:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/feature-flags/evaluate` | Evaluate one or more flags for the authenticated user and context. |
| GET | `/api/v1/feature-flags/bootstrap` | Return all flags relevant to the authenticated user and environment. |
| GET | `/api/v1/feature-flags/{key}` | Return a single evaluated flag for the authenticated user. |

## 3.3 Internal Service API

Internal services should not depend directly on repositories or cache implementation.

They should depend on `FeatureFlagService`.

Required service methods:

| Method | Purpose |
|---|---|
| `is_enabled` | Return boolean flag state for a user/context. |
| `evaluate` | Return detailed flag state, reason, variant, and metadata. |
| `evaluate_many` | Return multiple flags in one call. |
| `require_enabled` | Raise permission or feature-disabled error if flag is off. |
| `get_admin_flags` | Return admin-readable flag definitions. |
| `update_flag` | Update flag configuration with audit logging. |
| `enable_flag` | Enable flag with audit logging. |
| `disable_flag` | Disable flag with audit logging and cache invalidation. |

## 3.4 Response Contract

Flag evaluation responses should include:

- Flag key
- Enabled boolean
- Reason
- Environment
- Variant, if applicable
- Rollout bucket, if applicable
- User or role context, if applicable
- Dependencies evaluated
- Evaluated timestamp

## 3.5 Error Contract

The API should return clear errors for:

- Flag not found
- Invalid flag key
- Unauthorized management access
- Invalid environment
- Invalid rollout percentage
- Invalid dependency cycle
- Invalid assignment target
- Disabled feature access
- Cache unavailable fallback failure

---

# 4. Security Considerations

## 4.1 Role-Based Access Control

Recommended permissions:

| Action | Allowed Roles |
|---|---|
| Evaluate own flags | All authenticated users |
| Bootstrap own flags | All authenticated users |
| List flags | ADMIN, SUPER_ADMIN |
| Create flag | SUPER_ADMIN |
| Update flag | SUPER_ADMIN |
| Enable flag | SUPER_ADMIN |
| Disable flag | SUPER_ADMIN |
| Manage assignments | SUPER_ADMIN |
| View audit history | ADMIN, SUPER_ADMIN |

## 4.2 Live Trading Kill Switch

`live_trading.enabled` must be treated as a safety-critical flag.

Required controls:

- Only `SUPER_ADMIN` can enable live trading.
- Disabling live trading must take effect immediately.
- Redis TTL for live trading must be very short.
- Live order creation must re-check the flag immediately before execution.
- Disabling live trading must be audited with reason.
- Optional human confirmation should be required before enabling live trading.
- Optional secondary approval should be required for production environments.

## 4.3 AI Agent Safety

`ai_agents.enabled` should be coupled with the existing AI governance framework.

Required controls:

- AI agents cannot execute trades unless explicitly allowed by governance policy.
- AI agent actions must include audit chain metadata.
- AI agent decisions should include model version, policy version, and rationale.
- AI agent flags should be environment-scoped.
- AI agent rollout should start with internal users only.

## 4.4 News and Sentiment Safety

News and sentiment features should be gated independently.

Required controls:

- `news_analysis.enabled` gates news collection, classification, and scoring.
- `sentiment_analysis.enabled` gates sentiment collection and scoring.
- Both should be environment-scoped.
- Both should support staged rollout by user role or segment.
- API responses should not expose raw internal scoring unless the user has permission.

## 4.5 Experimental Feature Safety

`experimental_features.enabled` should be conservative.

Required controls:

- Disabled by default in production.
- Can be enabled for internal users or specific beta segments.
- Should not enable trading or financial risk by itself.
- Experimental features that affect trading must also pass their own domain-specific flag.

## 4.6 Audit and Traceability

All administrative changes must be audited.

Audit requirements:

- Actor identity
- Actor role
- IP address
- Flag key
- Old value
- New value
- Environment
- Reason
- Timestamp

For high-risk flags, evaluation results should also be auditable.

High-risk flags:

- `live_trading.enabled`
- `ai_agents.enabled`
- Any experimental feature that affects orders, positions, risk, or execution

## 4.7 Secrets and Sensitive Data

Flag metadata must not contain:

- API keys
- Exchange credentials
- JWT secrets
- Database passwords
- Model provider keys
- Private user data
- Internal tokens

Flag values should be boolean, numeric, or safe metadata only.

## 4.8 Rate Limiting

The evaluation API should be rate-limited.

Recommended limits:

- Authenticated user bootstrap: moderate limit.
- Single flag evaluation: moderate limit.
- Admin management endpoints: stricter limit.
- Internal service evaluation: allowlisted service path or local cache.

## 4.9 Failure Modes

Recommended default behavior:

| Flag Type | Failure Mode |
|---|---|
| Paper Trading | Fail closed if service cannot confirm state and paper trading is required. |
| Live Trading | Fail closed. If cache or DB is unavailable, block live orders. |
| AI Agents | Fail closed. |
| News Analysis | Fail closed or degrade to cached safe state. |
| Sentiment Analysis | Fail closed or degrade to cached safe state. |
| Experimental Features | Fail closed. |

---

# 5. Scalability Considerations

## 5.1 Low-Latency Evaluation

The system should optimize for fast evaluation because it may be called on trading, AI, news, sentiment, and UI rendering paths.

Recommended approach:

- Use Redis for hot flag state.
- Use PostgreSQL as source of truth.
- Use short TTLs for high-risk flags.
- Use local in-process cache for very hot global flags.
- Use cache invalidation on administrative changes.
- Batch evaluation for bootstrap endpoints.

## 5.2 Multi-Instance Consistency

APEX may run multiple backend instances behind Nginx.

Recommended consistency approach:

1. PostgreSQL stores the authoritative flag state.
2. Redis stores shared runtime state.
3. Backend instances use local in-process cache only for very short durations.
4. Redis pub/sub or revision marker invalidates local caches.
5. High-risk flags always revalidate against Redis or PostgreSQL before enforcement.

## 5.3 Redis Key Design

Recommended key categories:

- `feature_flag:global:{key}`
- `feature_flag:env:{environment}:{key}`
- `feature_flag:role:{role}:{key}`
- `feature_flag:user:{user_id}:{key}`
- `feature_flag:dependencies:{key}`
- `feature_flag:revision`

## 5.4 Rollout Strategy

The system should support gradual rollout.

Rollout types:

- Global on/off
- Environment-specific
- Role-specific
- User-specific
- Percentage rollout
- Time-window rollout
- Dependency-based rollout

Recommended rollout path for risky features:

1. Disabled globally.
2. Enabled for internal users.
3. Enabled for ADMIN users.
4. Enabled for limited TRADER beta segment.
5. Enabled for all TRADER users.
6. Enabled globally only after monitoring and risk review.

## 5.5 Environment Scoping

The system should support at least:

- `development`
- `staging`
- `production`

Environment behavior:

- Development can allow broader experimental access.
- Staging should mirror production rollout rules.
- Production should require stricter permissions and audit reasons.

## 5.6 Database Load

PostgreSQL should not be queried on every evaluation.

Recommended safeguards:

- Redis cache for evaluations.
- Batched admin queries.
- Indexed flag key and environment columns.
- Short audit writes only for state-changing actions.
- Optional asynchronous evaluation logging for high-volume metrics.

## 5.7 Observability

Feature flag system should emit metrics for:

- Flag evaluations per flag
- Flag evaluation latency
- Cache hit rate
- Cache miss rate
- Cache invalidation count
- Admin changes
- Disabled feature attempts
- Live trading block count
- AI agent disabled attempts
- Evaluation errors

## 5.8 Future Remote Configuration

Future expansion can include:

- Remote config provider
- Signed flag payloads
- Multi-region flag distribution
- Centralized feature flag UI
- Integration with CI/CD release gates
- Integration with AI governance policy engine

---

# 6. Gap Analysis

## 6.1 Current Gaps

| Gap | Current State | Required State |
|---|---|---|
| Centralized feature flag system | No flag service exists. | Central `FeatureFlagService` for all feature gating. |
| Flag storage | No feature flag tables exist. | PostgreSQL tables for flags, assignments, and audit history. |
| Flag cache | No Redis feature flag cache exists. | Redis-backed cache for low-latency evaluation. |
| Paper Trading gate | Paper trading endpoint exists but is not feature-flag gated. | `paper_trading.enabled` must gate paper-order creation. |
| Live Trading gate | Live order endpoint exists but is not feature-flag gated. | `live_trading.enabled` must act as a kill switch for real orders. |
| AI Agent gate | AI governance exists, but no feature flag gate exists. | `ai_agents.enabled` must gate AI agent orchestration and decisions. |
| News Analysis gate | News Analysis is planned but not implemented or gated. | `news_analysis.enabled` must gate news collection, analysis, and API. |
| Sentiment Analysis gate | Sentiment Analysis is planned but not implemented or gated. | `sentiment_analysis.enabled` must gate sentiment collection, analysis, and API. |
| Experimental Features gate | No experimental feature control exists. | `experimental_features.enabled` must gate unstable functionality. |
| Admin API | No feature flag admin endpoints exist. | Admin endpoints for create, update, enable, disable, assignments, and history. |
| Evaluation API | No feature flag evaluation endpoint exists. | Evaluation and bootstrap endpoints for clients and services. |
| Audit history | AuditLog exists but no flag-specific audit trail exists. | Flag changes and high-risk evaluations must be audited. |
| Role-based flag access | User roles exist but are not used for feature flags. | Role-scoped flag assignments and access rules. |
| Environment scoping | Environment config exists, but not for flags. | Environment-scoped flag state and rollout. |
| Kill switch | No global kill switch for live trading exists. | `live_trading.enabled` must immediately block live order execution. |
| Cache invalidation | No feature flag invalidation process exists. | Invalidate Redis and local caches on flag changes. |
| Dependency handling | No dependency model exists. | Support flag dependencies and prevent dependency cycles. |
| Rollout support | No rollout model exists. | Support percentage, user, role, and environment rollout. |
| Observability | No feature flag metrics exist. | Metrics for evaluation, cache, admin changes, and disabled attempts. |

## 6.2 Implementation Phases

### Phase 1: Core Flag Foundation

- Add domain models for flags, assignments, and audit history.
- Add repository and service layer.
- Add Redis cache.
- Add admin management API.
- Add evaluation API.
- Add initial required flags.

### Phase 2: Trading Enforcement

- Gate paper-order creation with `paper_trading.enabled`.
- Gate live order creation with `live_trading.enabled`.
- Make live trading fail closed.
- Add audit logs for live trading blocks and enable/disable actions.

### Phase 3: AI, News, and Sentiment Enforcement

- Gate AI agent orchestration with `ai_agents.enabled`.
- Gate news collection and analysis with `news_analysis.enabled`.
- Gate sentiment collection and analysis with `sentiment_analysis.enabled`.
- Add environment-scoped rollout for AI, news, and sentiment.

### Phase 4: Experimental Feature Controls

- Add `experimental_features.enabled`.
- Gate experimental UI and API endpoints.
- Add user or role-based beta assignment.
- Add monitoring for disabled experimental access attempts.

### Phase 5: Advanced Rollout and Observability

- Add percentage rollout.
- Add dependency rules.
- Add Redis pub/sub or revision invalidation.
- Add feature flag metrics and dashboards.
- Add runbooks for kill switch and rollout rollback.

## 6.3 Success Criteria

The feature flag system is complete when:

- All required flags exist.
- PostgreSQL stores flag definitions and history.
- Redis caches evaluated flags.
- Admins can create, update, enable, disable, and audit flags.
- Authenticated users can evaluate their allowed flags.
- Paper trading is gated by `paper_trading.enabled`.
- Live trading is gated by `live_trading.enabled` and fails closed.
- AI agents are gated by `ai_agents.enabled`.
- News analysis is gated by `news_analysis.enabled`.
- Sentiment analysis is gated by `sentiment_analysis.enabled`.
- Experimental features are gated by `experimental_features.enabled`.
- Flag changes are audited.
- Cache invalidation works across backend instances.
- Feature flag metrics are available for monitoring.
