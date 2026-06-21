# Definition of Done

## Code DoD

### Quality Standards
- Clean Architecture boundaries respected (no layer violations)
- Ruff linting passes with zero warnings
- Type checking passes (mypy with strict settings)
- No unused imports or dead code
- All functions have type hints
- All public APIs have docstrings

### Code Review
- Code reviewed by maintainer
- Review feedback addressed
- Commit message follows conventional commits format
- No merge conflicts

### Complexity
- Cyclomatic complexity < 10 per function
- No deeply nested code (> 4 levels)
- Functions do one thing (SRP)
- No magic numbers or strings (use named constants)

## Architecture DoD

### Layer Boundaries
- Domain layer has zero external imports
- Application layer imports only from Domain
- Infrastructure imports only from Domain (interfaces)
- Presentation imports only from Application
- No circular dependencies

### Design Patterns
- Repository pattern used for data access
- Unit of Work for transactions
- Dependency injection (constructor injection)
- Domain events for cross-module communication
- DTOs at API boundaries

### Structure
- Code follows folder architecture defined in docs
- Files named according to naming rules
- Modules cohesive and loosely coupled
- No feature envy (code in wrong module)

## Testing DoD

### Coverage
- Unit tests written for all new code
- Integration tests for new integrations
- Overall coverage >= 80%
- Domain coverage >= 90%
- No coverage drop from previous baseline

### Test Quality
- Tests are deterministic (no flaky tests)
- Tests are independent
- Tests use meaningful assertions
- Edge cases and error paths tested
- Tests run in CI

### E2E
- Critical user flows covered by E2E tests
- E2E tests pass in staging
- No skipped E2E tests

## Documentation DoD

### Architecture
- Architecture documentation updated for changes
- New modules documented in module architecture
- New patterns added to project conventions

### API
- OpenAPI docs generated and accurate
- Breaking changes documented
- Deprecation notices added

### User-Facing
- README updated for user-facing changes
- CHANGELOG updated
- Configuration changes documented

## Security DoD

### Code Security
- Security scan passes (pip-audit)
- No secrets in code or config files
- Input validation on all endpoints
- Authentication on protected routes
- Authorization checks on sensitive operations

### Dependencies
- No known critical vulnerabilities
- Dependencies pinned to exact versions
- Dependabot alerts resolved
- License compliance verified

### Secrets
- API keys not in logs
- Secrets not in error messages
- Secrets rotated if exposed
- Keys scoped to minimum permissions

## Performance DoD

### Response Time
- API p95 latency < 200ms
- Database queries optimized (indexes used)
- No N+1 query problems
- Cache strategy implemented where appropriate

### Resource Usage
- Memory usage stable (no leaks)
- Connection pools properly sized
- No resource exhaustion under load
- Graceful degradation on failures

### Load Testing
- System handles target RPS
- No degradation under sustained load
- Recovery from spike verified

## Deployment DoD

### CI/CD
- CI pipeline green
- All tests pass in CI
- Build succeeds
- Deployment succeeds

### Infrastructure
- Health checks pass
- Configuration validated
- Environment variables set
- Secrets available in target environment

### Monitoring
- Metrics exported
- Alerts configured
- Dashboards updated
- Logs centralized

## Operational DoD

### Runbook
- Deployment runbook updated
- Rollback procedure documented
- Troubleshooting guide updated
- On-call runbook current

### Backup
- Backup procedure verified
- Restore procedure tested
- Backup schedule configured
- Retention policy set

### Communication
- Stakeholders notified of changes
- Deployment window communicated
- Rollback plan shared
