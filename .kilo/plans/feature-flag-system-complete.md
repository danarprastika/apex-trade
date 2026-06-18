# Feature Flag System - Complete Design

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FEATURE FLAG SYSTEM ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐      │
│  │   Feature Flag   │   │   Feature Flag     │   │   Audit Service    │      │
│  │   API            │   │   Service          │   │                    │      │
│  │   (Endpoints)    │──▶│   (Evaluation)     │──▶│   (Logging)        │      │
│  └──────────────────┘   └─────────┬──────────┘   └──────────────────┘      │
│                                   │                                        │
│                                   ▼                                        │
│  ┌──────────────────┐   ┌──────────────────┐                              │
│  │   Redis Cache    │   │   PostgreSQL       │                              │
│  │   (Hot State)    │   │   (Source of      │                              │
│  └──────────────────┘   │   Truth)           │                              │
│                          └────────────────────┘                              │
│                                   │                                         │
│  ┌──────────────────┐   ┌──────────▼──────────┐                              │
│  │   Enforcement    │   │   Enforcement       │                              │
│  │   Points         │◀──│   Points            │                              │
│  │   (Trading, AI,  │   │   (Trading, AI,    │                              │
│  │   News, Sentiment)│   │   News, Sentiment) │                              │
│  └──────────────────┘   └─────────────────────┘                              │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **Low-Latency** | Redis cache for evaluation; <10ms response target |
| **Consistent** | PostgreSQL source of truth; cache invalidation on changes |
| **Fail-Safe** | Kill switches default to fail-closed |
| **Auditable** | All administrative changes logged with full context |
| **Scalable** | Stateless service; horizontal scaling support |

---

## 2. Required Flags

### 2.1 Core Feature Flags

| Flag Key | Name | Default | Enforcement Point | Kill Switch |
|----------|------|---------|-------------------|-------------|
| `paper_trading.enabled` | Paper Trading | `true` | PaperTradingService | No |
| `live_trading.enabled` | Live Trading | `false` | ExecutionService | Yes |
| `ai_agents.enabled` | AI Agents | `false` | AI Orchestration | Yes |
| `news_analysis.enabled` | News Analysis | `false` | News Collector/API | No |
| `sentiment_analysis.enabled` | Sentiment Analysis | `false` | Sentiment Collector/API | No |

### 2.2 Flag Configuration Properties

```python
class FeatureFlagSpec:
    key: str                    # Unique identifier
    name: str                   # Human-readable name
    default_enabled: bool       # Default state
    is_kill_switch: bool        # Fail-closed behavior
    failure_mode: str          # fail_closed | fail_open
    environment_scope: str     # development | staging | production
    allowed_roles: list[str]   # Roles that can manage
    ttl_seconds: int          # Cache TTL
    metrics_enabled: bool     # Emit evaluation metrics
```

---

## 3. Storage Strategy

### 3.1 PostgreSQL Schema

**feature_flags table:**
```sql
id UUID PK
key VARCHAR(100) UNIQUE NOT NULL
name VARCHAR(100) NOT NULL
description TEXT
enabled BOOLEAN NOT NULL DEFAULT false
environment VARCHAR(20) NOT NULL DEFAULT 'development'
owner VARCHAR(100)
metadata JSONB
is_kill_switch BOOLEAN NOT NULL DEFAULT false
failure_mode VARCHAR(20) NOT NULL DEFAULT 'fail_closed'
created_at TIMESTAMP
updated_at TIMESTAMP
```

**feature_flag_assignments table:**
```sql
id UUID PK
flag_id UUID FK NOT NULL
target_type VARCHAR(20) NOT NULL  -- user, role, segment
target_id VARCHAR(100)            -- user_id or segment_id
target_role VARCHAR(20)           -- role name
rollout_percentage NUMERIC(5,2)   -- 0-100
environment VARCHAR(20)
enabled BOOLEAN NOT NULL DEFAULT true
metadata JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
```

**feature_flag_audit_logs table:**
```sql
id SERIAL PK
flag_id UUID NOT NULL
flag_key VARCHAR(100) NOT NULL
action VARCHAR(50) NOT NULL    -- create, update, enable, disable
old_value JSONB
new_value JSONB
actor_user_id UUID
actor_role VARCHAR(20)
ip_address VARCHAR(100)
reason VARCHAR(500)
created_at TIMESTAMP
```

### 3.2 Redis Cache Key Design

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `feature_flag:flag:{key}` | Configurable per flag | Cached evaluation result |
| `feature_flag:user:{user_id}:{key}` | 60-300s | User-scoped override |
| `feature_flag:role:{role}:{key}` | 60-300s | Role-scoped assignment |
| `feature_flag:revision` | N/A | Global revision for invalidation |

### 3.3 Cache TTL Strategy

| Flag Type | TTL | Rationale |
|-----------|-----|-----------|
| `live_trading.enabled` | 10s | Safety-critical; fast propagation |
| `ai_agents.enabled` | 30s | Governance-aligned; moderate latency |
| `paper_trading.enabled` | 60s | Low risk; reasonable caching |
| `news_analysis.enabled` | 60s | External data; cached acceptable |
| `sentiment_analysis.enabled` | 60s | External data; cached acceptable |

---

## 4. API Design

### 4.1 Admin Management Endpoints

```
GET    /api/v1/admin/feature-flags
       Query: ?enabled=true&environment=production

GET    /api/v1/admin/feature-flags/{key}

POST   /api/v1/admin/feature-flags
       Body: FeatureFlagCreate

PUT    /api/v1/admin/feature-flags/{key}
       Body: FeatureFlagUpdate

PATCH  /api/v1/admin/feature-flags/{key}/enable
       Body: { reason: string }

PATCH  /api/v1/admin/feature-flags/{key}/disable
       Body: { reason: string }

GET    /api/v1/admin/feature-flags/{key}/history
       Query: ?limit=100

POST   /api/v1/admin/feature-flags/{key}/assignments
       Body: AssignmentCreate

DELETE /api/v1/admin/feature-flags/{key}/assignments/{id}
```

### 4.2 Evaluation Endpoints

```
POST   /api/v1/feature-flags/evaluate
       Body: { flags: ["key1", "key2"] }
       Response: { flags: [FeatureFlagEvaluateResponse] }

GET    /api/v1/feature-flags/bootstrap
       Response: { flags: [...], environment: string, user_id: string }

GET    /api/v1/feature-flags/{key}
       Response: FeatureFlagEvaluateResponse
```

### 4.3 Service API (Internal)

```python
class FeatureFlagService:
    def is_enabled(key: str, user: User | None = None, environment: str | None = None) -> bool
    def evaluate(key: str, user: User | None = None, environment: str | None = None) -> FeatureFlagEvaluationResult
    def evaluate_many(keys: list[str], user: User | None = None, environment: str | None = None) -> list[FeatureFlagEvaluationResult]
    def require_enabled(key: str, user: User | None = None, environment: str | None = None) -> FeatureFlagEvaluationResult
    def get_admin_flags(environment: str | None = None) -> list[FeatureFlag]
    def update_flag(key: str, payload: Any, actor: User, ip_address: str | None = None) -> FeatureFlag
    def enable_flag(key: str, actor: User, ip_address: str | None = None, reason: str | None = None) -> FeatureFlag
    def disable_flag(key: str, actor: User, ip_address: str | None = None, reason: str | None = None) -> FeatureFlag
```

---

## 5. Security Considerations

### 5.1 Role-Based Access Control

| Action | Required Role |
|--------|---------------|
| Evaluate own flags | All authenticated users |
| Bootstrap own flags | All authenticated users |
| List flags | ADMIN, SUPER_ADMIN |
| Create flag | SUPER_ADMIN |
| Update flag | SUPER_ADMIN |
| Enable flag | SUPER_ADMIN |
| Disable flag | SUPER_ADMIN |
| Manage assignments | SUPER_ADMIN |
| View audit history | ADMIN, SUPER_ADMIN |

### 5.2 Live Trading Kill Switch

**Critical Security Controls:**
- Only `SUPER_ADMIN` can enable live trading
- Disabling takes effect within 10 seconds (cache TTL)
- Live order creation must re-check flag immediately before execution
- All disable/enable actions audited with reason
- Optional secondary approval for production environments

### 5.3 AI Agent Safety

**Integration with AI Governance:**
- `ai_agents.enabled` gates agent orchestration and decisions
- AI agents cannot execute trades without explicit governance approval
- All agent actions include audit chain metadata
- Agent rollout starts with internal users only

### 5.4 News and Sentiment Safety

**Isolation Controls:**
- Features gated independently
- Environment-scoped rollout
- Role-based staged access
- Raw scoring data not exposed without permission

### 5.5 Experimental Features

**Conservative Controls:**
- Disabled by default in production
- Internal/beta user access only
- Cannot enable trading or financial risk by itself
- Trading features require additional domain-specific flags

### 5.6 Audit and Traceability

All administrative actions log:
- Actor identity and role
- IP address
- Flag key and old/new values
- Environment
- Reason for change
- Timestamp

### 5.7 Failure Modes

| Flag Type | On Failure | Behavior |
|-----------|------------|----------|
| `live_trading.enabled` | Cache/DB unavailable | Block all live orders |
| `paper_trading.enabled` | Cache/DB unavailable | Block if required |
| `ai_agents.enabled` | Cache/DB unavailable | Block AI actions |
| `news_analysis.enabled` | Cache/DB unavailable | Fail closed or cached state |
| `sentiment_analysis.enabled` | Cache/DB unavailable | Fail closed or cached state |

---

## 6. Enforcement Points

### 6.1 Paper Trading Enforcement

**Location:** `PaperTradingService.execute_order()`

**Check:** Before order creation, verify `paper_trading.enabled` is true

**Failure:** Raise `FeatureDisabledError` if flag disabled

### 6.2 Live Trading Enforcement

**Location:** `ExecutionService.submit_order()`

**Check:** Before any live order submission, verify `live_trading.enabled` is true

**Failure:** Block order, return `FeatureDisabledError`, audit the attempt

### 6.3 AI Agent Enforcement

**Location:** AI orchestration entry point

**Check:** Before agent execution, verify `ai_agents.enabled` is true

**Failure:** Block agent action, return error to caller

### 6.4 News Analysis Enforcement

**Location:** News collector and News API endpoints

**Check:** Before collection/classification, verify `news_analysis.enabled` is true

**Failure:** Return empty results or 403 Forbidden

### 6.5 Sentiment Analysis Enforcement

**Location:** Sentiment collector and Sentiment API endpoints

**Check:** Before collection/scoring, verify `sentiment_analysis.enabled` is true

**Failure:** Return empty results or 403 Forbidden

---

## 7. Implementation Roadmap

### Phase 1: Core Foundation (Complete)
- [x] Domain models (FeatureFlag, FeatureFlagAssignment, FeatureFlagAuditLog)
- [x] Repository layer (FeatureFlagRepository)
- [x] Cache layer (FeatureFlagCache with Redis)
- [x] Service layer (FeatureFlagService with evaluation)
- [x] Schemas (Pydantic models)

### Phase 2: Trading Enforcement (In Progress)
- [ ] Integrate `paper_trading.enabled` into PaperTradingService
- [ ] Integrate `live_trading.enabled` into ExecutionService
- [ ] Add fail-closed behavior for kill switches
- [ ] Add audit logging for blocked attempts

### Phase 3: AI & Intelligence Enforcement
- [ ] Integrate `ai_agents.enabled` into AI orchestration
- [ ] Integrate `news_analysis.enabled` into news collector
- [ ] Integrate `sentiment_analysis.enabled` into sentiment collector
- [ ] Add environment-scoped rollout

### Phase 4: Advanced Features
- [ ] Add percentage rollout support
- [ ] Add dependency rules
- [ ] Add Redis pub/sub invalidation
- [ ] Add metrics dashboard

---

## 8. Observability

### 8.1 Metrics to Emit

| Metric | Description |
|--------|-------------|
| `flag_evaluations_total` | Count of evaluations per flag |
| `flag_evaluations_latency_ms` | Evaluation response time |
| `flag_cache_hit_rate` | Cache hit percentage |
| `flag_cache_miss_rate` | Cache miss percentage |
| `flag_admin_changes_total` | Administrative changes |
| `flag_disabled_attempts_total` | Blocked feature access attempts |
| `flag_live_trading_blocked_total` | Live trading block count |
| `flag_ai_disabled_attempts_total` | AI agent disable count |