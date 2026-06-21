# Definition of Done

## 1. Task-Level DoD (Definition of Done)

Every user story, task, or engineering task must meet ALL criteria below before being marked complete.

### 1.1 Code Quality
- [ ] Written according to the standards in [Coding Standards](./07-coding-standards.md)
- [ ] Type hints on all public functions and methods
- [ ] Formatted with `ruff` (no style issues)
- [ ] Linted with `ruff check` (no errors)
- [ ] Type-checked with `mypy` (no errors)

### 1.2 Testing
- [ ] Unit tests written for new/changed logic
- [ ] Test coverage ≥ 80% for new code
- [ ] All new tests pass in CI
- [ ] Existing tests still pass (no regressions)
- [ ] Edge cases covered in tests
- [ ] Tests documented in Markdown (comment/string explaining purpose)

### 1.3 Documentation
- [ ] Docstrings added for all new public methods and classes
- [ ] Architecture decisions documented (ADR if applicable)
- [ ] API documentation auto-generated (for new endpoints)
- [ ] README|user guide updated if user-facing change

### 1.4 Security
- [ ] Input validation applied at all boundaries
- [ ] No secrets or credentials committed
- [ ] Sensitive data not logged
- [ ] Error messages don't leak internal information

### 1.5 Dependency Management
- [ ] Dependencies listed in `pyproject.toml` with version pins
- [ ] No circular dependencies introduced (verified by `import-linter`)
- [ ] Depedt committed to, with issue link referencing meeting notes

### 1.6 Deployment
- [ ] Works in Docker Compose (startup, shutdown, restart)
- [ ] Health check passes
- [ ] Docker image builds successfully
- [ ] No breaking changes to existing compose file

## 2. Story-Level DoD

User stories are complete when:

### 2.1 Functional Completeness
- [ ] All acceptance criteria met (per PRM)
- [ ] User can accomplish stated goal end-to-end
- [ ] Edge cases handled (empty, null, errors)
- [ ] Error messages user-friendly

### 2.2 Integration
- [ ] Works end-to-end with real database
- [ ] Works end-to-end with real Redis (if applicable)
- [ ] Works with real external APIs (in testing environment)
- [ ] All component interactions verified

### 2.3 Observability
- [ ] Logs emitted with structured format
- [ ] Logs contain meaningful context (not just text)
- [ ] Metrics emitted where applicable
- [ ] Health check reflects new capability

### 2.4 Rollback
- [ ] Can be disabled via feature flag (if experimental)
- [ ] Database migration reversible (if schema change)
- [ ] Zero-downtime deployment possible

## 3. Sprint-Level DoD

A sprint is complete when:

### 3.1 All Stories Complete
- [ ] All planned stories meet story-level DoD
- [ ] No critical bugs left open
- [ ] Known technical debt logged (not blocking)

### 3.2 Quality Gates
- [ ] All tests pass locally and in CI
- [ ] Coverage ≥ 80% overall
- [ ] No lint errors
- [ ] No type errors
- [ ] Docker Compose converges (all services healthy)
- [ ] Health checks pass on all services

### 3.3 Documentation
- [ ] Architecture Decision Records (ADRs) updated if needed
- [ ] Changelog updated for sprint
- [ ] README reflects new features or setup steps

### 3.4 Demo Readiness
- [ ] Feature can be demonstrated (running locally or in staging)
- [ ] Acceptance criteria verifiable in demo
- [ ] Known limitations documented

## 4. Security DoD

Every release must meet security criteria:

### 4.1 Code Security
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] No credentials or secrets in code
- [ ] Sensitive data not logged in plaintext

### 4.2 Infrastructure Security
- [ ] TLS 1.3 enabled for all external traffic
- [ ] Nginx security headers configured
- [ ] Docker containers run as non-root
- [ ] Secrets managed via Docker secrets or vault

### 4.3 Dependency Security
- [ ] No critical/high vulnerabilities (via `pip-audit`)
- [ ] Dependencies pinned to exact versions
- [ ] Dependencies updated to latest patch versions within 30 days
- [ ] SBOM (Software Bill of Materials) generated for release

### 4.4 Authentication & Authorization
- [ ] Authentication required for protected endpoints
- [ ] Authorization enforced (user can only access own data)
- [ ] Session tokens have expiry
- [ ] Rate limiting in place for public-facing endpoints

## 5. Performance DoD

### 5.1 API Performance
- [ ] Latency P95 < 500ms for API endpoints
- [ ] Latency P99 < 2000ms for API endpoints
- [ ] Database queries optimized (no N+1)
- [ ] Caching strategy defined and implemented (if applicable)

### 5.2 System Performance
- [ ] Memory usage < 512MB per service (baseline)
- [ ] CPU usage < 80% under normal load
- [ ] No memory leaks detected (24-hour soak test)
- [ ] Graceful degradation under high load

### 5.3 Resource Efficiency
- [ ] Docker images < 1GB (backend), < 100MB (frontend)
- [ ] Database queries per request < 10
- [ ] Redis hit rate > 80% (if using cache)

## 6. Data Integrity DoD

### 6.1 Database
- [ ] All tables have proper indexes (no missing indexes on foreign keys)
- [ ] Constraints enforced at database level
- [ ] No orphaned records after tests
- [ ] Migrations are idempotent and reversible

### 6.2 Consistency
- [ ] Domain invariants enforced in code
- [ ] Transactions used for multi-table operations
- [ ] Eventual consistency strategies documented
- [ ] No data duplication without justification

### 6.3 Backups
- [ ] Backup strategy implemented and tested
- [ ] Backup restore procedure documented
- [ ] RPO < 1 hour (maximum 1 hour of data loss)
- [ ] RTO < 4 hours (maximum 4 hours to restore)

## 7. Deployment DoD

### 7.1 Containerization
- [ ] Docker images built successfully
- [ ] Images pushed to registry
- [ ] Images use multi-stage builds (minimal base)
- [ ] Containers run as non-root
- [ ] Read-only filesystem (where possible)

### 7.2 Orchestration
- [ ] Docker Compose converges cleanly
- [ ] All services health check passing
- [ ] Configurable via environment variables
- [ ] Secrets managed securely (not in config files)

### 7.3 Monitoring
- [ ] Health check endpoints implemented
- [ ] Logs structured (JSON) and parseable
- [ ] Metrics exposed for critical operations
- [ ] Alerting defined for critical failures

### 7.4 Rollback
- [ ] Rollback procedure documented
- [ ] Rollback tested (can go from vN to vN-1)
- [ ] Data migrations reversible
- [ ] Zero-data-loss rollback verified

## 8. Release DoD

### 8.1 Pre-Release Checklist
- [ ] All tests pass
- [ ] All security scans pass
- [ ] Performance benchmarks met
- [ ] Documentation complete and accurate
- [ ] Changelog reflects all changes
- [ ] Release tag created with semantic version
- [ ] Docker images tagged and pushed
- [ ] Deployment verified in staging

### 8.2 Post-Release
- [ ] Production health checks passing
- [ ] No unexpected errors in logs
- [ ] Key business metrics within expected range
- [ ] Stakeholders notified of release
- [ ] Rollback Ready: Backout documented for production (if deploy fails)
- [ ] Communication: Status page or internal notice sent if known outage
- [ ] Alerting: Production alerts validated for new behavior
- [ ] Feedback loop: User/stakeholder feedback requested
- [ ] Post-mortem (if production issue): Root cause and remediation documented

### 8.3 Monitoring & Observability Readiness
- [ ] Dashboards are updated for new features/dashboards
- [ ] Telemetry added (events, traces, logs)
- [ ] Alerts defined for new failure modes
- [ ] On-call runbook updated

### 8.4 Release Communication
- [ ] Internal: Announce upcoming release timeline and scope
- [ ] External: Changelog published for users
- [ ] Stakeholders: Notify business owners of deployment windows
- [ ] Risk Boost: Potential business/tech risk acknowledged and mitigated
- [ ] Rollback Info: Defined rollback steps for this release
- [ ] Safety Notes: Include any manual intervention or unexpected TTH notes

### 8.5 Reliability & Safety
- [ ] Safety reviewed: Review process completed
- [ ] Rollback validated: Tested rollback path end-to-end
- [ ] Data integrity: Schema/data changes backward compatible
- [ ] Env flags ready: Feature flags configured for gradual rollout
- [ ] Backups confirmed: Restore point verified

### 8.6 MVP-Specific DoD
- [ ] No external telemetry invites (privacy-first, no IP logging by default)

## 9. Exception Process

When a task cannot fully meet DoD, it requires **explicit approval** from project leadership.

### 9.1 Exception Request Format
```markdown
## DoD Exception Request
**Task**: <story/task ID>
**Missing Criteria**: <which DoD items not met>
**Reason**: <why extension is needed>
**Risk**: <impact of not meeting DoD>
**Mitigation**: <how risk is handled>
**Plan to Resolve**: <when/how DoD will be met>
**Approver**: <name>
```

### 9.2 Exception Categories

| Category | Approval Required | Max Duration |
|----------|-------------------|--------------|
| Technical Debt | Tech Lead | 1 sprint |
| Missing Tests | QA Lead | 2 sprints |
| Security Gap | Security Reviewer | 1 sprint (critical: immediate) |
| Documentation | Tech Writer | 1 sprint |

## 10. DoD Review Process

### 10.1 Review Cadence
- **Pre-sprint**: Review DoD criteria with team
- **Story completion**: Self-assessment against DoD
- **Sprint review**: Review completeness with team
- **Monthly**: Review DoD itself for relevance

### 10.2 DoD Improvement
- Team can propose DoD changes
- Changes require team consensus
- Document rationale for each criterion
- Review DoD quarterly for relevance

## 11. DoD Metrics

Track these metrics to measure DoD effectiveness:

- **Defect Escape Rate**: Bugs found in production vs. total
- **Rework Percentage**: Stories requiring rework after completion
- **Story Completion Rate**: Stories completed vs. committed
- **Test Coverage Trend**: % coverage over time
- **Build Success Rate**: % successful CI builds
- **Deployment Success Rate**: % successful deployments

Target: ≥ 90% on all metrics.
