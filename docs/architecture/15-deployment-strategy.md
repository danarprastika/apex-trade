# Deployment Strategy

## Deployment Architecture

### Target Environment
- Single Linux VPS (Ubuntu 22.04 LTS)
- Docker Engine + Docker Compose
- Nginx reverse proxy
- No orchestration platform (Kubernetes overkill)

### Service Topology

Internet -> Nginx (SSL, Port 443) -> Docker Network
    +-- Backend (FastAPI, Port 8000)
    +-- Frontend (Nginx, Port 3000)
    +-- PostgreSQL (Port 5432)
    +-- Redis (Port 6379)

### Networking
- All services on private Docker network
- Nginx as only exposed port
- No direct database/Redis access from outside

## Docker Image Strategy

### Base Images
- Backend: python:3.12-slim (Debian-based, minimal)
- Frontend: node:20-alpine (Alpine, minimal)
- Nginx: nginx:alpine (Alpine, minimal)

### Multi-Stage Builds
- Stage 1: Build dependencies
- Stage 2: Runtime with minimal image
- Target image size: Backend < 200MB, Frontend < 100MB

### Tagging Strategy
- latest: Most recent production version
- {commit-sha}: Specific commit for rollback
- {version}: Semantic version tag

## Docker Compose Production

### Services
- nginx: SSL termination, reverse proxy
- backend: FastAPI application with health checks
- frontend: Static file serving
- postgres: PostgreSQL with persistent volumes
- redis: Redis with persistent volumes

### Volumes
- ./data/postgres: Database persistence
- ./data/redis: Cache persistence
- ./ssl: SSL certificates
- ./logs: Application logs

## CI/CD Pipeline (GitHub Actions)

### Workflow: CI
- Lint: Ruff check, mypy type check
- Test: Run full test suite
- Build: Build Docker images
- Security: pip-audit scan

### Workflow: CD
- Trigger: Push to main branch
- Steps: Build images -> SSH to VPS -> Pull images -> Restart services -> Run migrations
- Manual approval for production

## Database Migration Strategy

### Tool: Alembic
- Auto-generate migrations from model changes
- Manual review required before commit
- Migrations versioned in git
- Rollback scripts for each migration

### Migration Process
1. Developer creates migration: alembic revision --autogenerate
2. Review migration SQL
3. Commit to repository
4. CI validates migration
5. CD applies migration on deploy
6. Backup before migration

### Rollback
- Rollback one migration: alembic downgrade -1
- Rollback to specific version: alembic downgrade abc123

## Zero-Downtime Deployment

### Current Approach (Single Instance)
- Fast container restart (<5 seconds)
- Graceful shutdown with timeout
- Health check before traffic routing
- Rolling restart for multi-container

### Graceful Shutdown
- Stop accepting new connections
- Finish processing in-flight requests
- Close database connections
- Flush logs

### Health Checks
- /health endpoint for liveness
- /ready for readiness
- Database connectivity check
- Redis connectivity check
- Exchange API connectivity

## Rollback Procedures

### Automated Rollback
1. Monitor deployment health
2. If health checks fail for 2 minutes, auto-rollback
3. Redeploy previous SHA tag
4. Alert on-call

### Manual Rollback
1. SSH to VPS
2. Navigate to project directory
3. Check current version
4. Rollback to previous image tag
5. Verify health

### Database Rollback
- Never auto-rollback database migrations
- Manual review required
- Restore from backup if needed
- Document rollback procedure

## Backup Strategy

### PostgreSQL Backups
- Daily full backup with pg_dump
- Continuous WAL archiving
- Weekly restore test

### Retention
- Daily backups: 30 days
- Weekly backups: 12 weeks
- Monthly backups: 12 months

### Backup Verification
- Weekly restore test
- Verify backup integrity
- Test point-in-time recovery
