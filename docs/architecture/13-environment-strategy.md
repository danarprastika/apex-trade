# Environment Strategy

## Environment Definitions

### Local
- Purpose: Developer machine, rapid iteration
- Database: SQLite (file-based)
- Cache: In-memory or local Redis
- API Keys: Sandbox/paper trading keys
- Debug: Full debug logging enabled
- Hot Reload: Enabled for frontend and backend

### Development
- Purpose: Shared development, integration testing
- Database: PostgreSQL (Docker)
- Cache: Redis (Docker)
- API Keys: Development/sandbox keys
- Debug: Info-level logging
- Hot Reload: Backend hot reload

### Staging
- Purpose: Pre-production validation
- Database: PostgreSQL (VPS or cloud)
- Cache: Redis (VPS or cloud)
- API Keys: Production keys (limited scope)
- Debug: Warning-level logging
- Hot Reload: Disabled

### Production
- Purpose: Live trading, real funds
- Database: PostgreSQL (primary + optional replica)
- Cache: Redis (persistent)
- API Keys: Production keys (full scope)
- Debug: Error-level logging only
- Hot Reload: Disabled

## Environment Variables Per Environment

### Local (.env.local)
- QUANTX_ENV=local
- DATABASE_URL=sqlite:///./quantx_local.db
- REDIS_URL=redis://localhost:6379/0
- QUANTX_DEBUG=true
- QUANTX_LOG_LEVEL=DEBUG
- FEATURE_PAPER_TRADING=true

### Development (.env.development)
- QUANTX_ENV=development
- DATABASE_URL=postgresql+asyncpg://quantx:devpass@db:5432/quantx_dev
- REDIS_URL=redis://redis:6379/0
- QUANTX_DEBUG=false
- QUANTX_LOG_LEVEL=INFO
- FEATURE_PAPER_TRADING=true

### Production (.env.production)
- QUANTX_ENV=production
- DATABASE_URL=postgresql+asyncpg://quantx:prodpass@db:5432/quantx
- REDIS_URL=redis://redis:6379/0
- QUANTX_DEBUG=false
- QUANTX_LOG_LEVEL=ERROR
- FEATURE_PAPER_TRADING=false

## Local Development Setup

### Prerequisites
- Docker Desktop or Docker Engine
- Docker Compose
- Python 3.12+
- Node.js 20+
- Git

### Quick Start
1. Clone repository
2. Copy environment template
3. Start all services with docker-compose
4. Install backend and frontend dependencies
5. Run database migrations
6. Start backend and frontend with hot reload

### Development Tools
- Database admin: pgAdmin or DBeaver
- Cache inspector: Redis Insight
- API testing: Postman or Bruno
- Logs: docker-compose logs -f

## Environment Isolation Principles

### Network Isolation
- Each environment in separate network
- No cross-environment communication
- Firewall rules per environment

### Data Isolation
- Separate databases per environment
- No data sharing between environments
- Production data never used in dev/staging

### Credential Isolation
- Separate API keys per environment
- Production keys never in lower environments
- Key rotation independent per environment

## Data Management Per Environment

### Local
- SQLite database (ephemeral)
- Seed data on first run
- Can be reset freely
- No sensitive data

### Development
- PostgreSQL container
- Synthetic market data
- Test accounts with sandbox exchanges
- Reset via docker-compose down -v

### Staging
- PostgreSQL (same schema as production)
- Anonymized production data
- Read-only production replica (optional)
- Weekly refresh from production backup

### Production
- PostgreSQL with WAL archiving
- Live trading data
- Daily automated backups
- Point-in-time recovery (PITR)

## Environment Promotion

### Promotion Flow
Local -> Development -> Staging -> Production
   Manual    Auto       Auto       Manual
   commit    test       deploy     approval

### Promotion Criteria
1. All tests pass
2. Security scan passes
3. Performance benchmarks met
4. Documentation updated
5. Manual review for production

### Promotion Process
1. Merge to main branch
2. CI runs all checks
3. Deploy to staging
4. Run smoke tests
5. Manual approval for production
6. Deploy to production
7. Post-deployment verification

## Hotfix Workflow

### Steps
1. Create hotfix branch from main
2. Implement minimal fix
3. Fast-track CI (skip optional checks)
4. Deploy to production immediately
5. Merge back to main

### Fast-Track CI
- Lint only
- Critical tests only
- Skip performance tests
- Skip integration tests (unless related)

### Post-Hotfix
- Full test suite on next regular deploy
- Post-mortem if critical
- Add regression test
