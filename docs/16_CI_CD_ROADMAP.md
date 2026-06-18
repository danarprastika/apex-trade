# CI/CD Roadmap

Version: 0.1
Status: Draft
Document Type: Infrastructure / CI-CD
This roadmap does not generate executable code or workflow YAML content.

---

# 0 Current Repository Review

Repository: apex-trade
Branching strategy: main, develop, feature/\*, as referenced in Documentation 10_DEPLOYMENT_ARCHITECTURE.md.

Current state:

- No .github directory or GitHub Actions workflows currently exist.
- docker-compose.yml defines services: postgres, redis, backend, celery, scheduler, frontend, telegram-bot, nginx.
- backend/requirements.txt includes: FastAPI, SQLAlchemy, Redis, Celery, pytest, pytest-asyncio, ccxt, apscheduler, structlog.
- frontend/package.json contains dev, build, and preview scripts. No test or lint scripts exist. No test or lint devDependencies are present.
- Dockerfiles exist for backend, frontend, telegram-bot, and infrastructure/nginx.
- backend/tests contains test modules for: health, audit middleware, exchange and risk, event bus, exchange abstraction, strategy plugins, and backtest.
- Documentation 10_DEPLOYMENT_ARCHITECTURE.md mentions a GitHub Actions pipeline (Push -> Tests -> Build -> Deploy) but no implementation exists.
- .gitignore ignores .env, node_modules, dist, caches, logs, and coverage artifacts.

---

# 1 Missing Components

- .github/workflows/ directory with CI pipeline definitions.
- Backend lint configuration (ruff or equivalent).
- Frontend test framework and lint tooling (Vitest, ESLint, or equivalent).
- .dockerignore files to exclude development artifacts from Docker build context.
- Dependabot configuration for automated dependency updates.
- GitHub repository secrets documentation describing required secrets and their environment scopes.
- CI runbook documenting how to interpret workflow results, rerun failed jobs, and escalate failures.
- Branch protection rules and required status checks configuration for main and develop branches.

---

# 2 Workflow Structure

## 2.1 ci.yml

Trigger events: pull_request (all branches), push to feature/\*, push to develop.

Jobs:

- Backend Lint: Run static analysis on backend Python code using configured linter. Report failures as PR annotations.
- Backend Test: Run pytest with asyncio support against configured test suite. Test modules cover health, audit middleware, exchange and risk, event bus, exchange abstraction, strategy plugins, and backtest.
- Frontend Lint: Run configured frontend linter against src/ and configuration files.
- Frontend Type Check: Run TypeScript compiler in noEmit mode to verify type correctness.
- Frontend Build: Run production build to verify bundling succeeds.
- Frontend Test: Execute frontend unit and integration tests once test framework and dependencies are added to package.json.
- Security Scan: Run dependency vulnerability scan on backend Python dependencies and frontend JavaScript dependencies. Fail on critical or high severity vulnerabilities.
- Docker Build: Build Docker images for backend, frontend, telegram-bot, and nginx to verify Dockerfiles are valid and builds succeed. Push is not performed in this workflow.

## 2.2 docker-push.yml

Trigger events: push to main, push to develop, tags matching v\*.

Jobs:

- Docker Build and Push: Build Docker images for backend, frontend, telegram-bot, and nginx. Tag images with commit SHA, branch name, and semantic version tags. Push to GitHub Container Registry or configured registry. Login uses GitHub Actions OIDC or stored registry credentials via repository secrets.

## 2.3 security.yml

Trigger events: schedule (weekly), pull_request targeting main or develop, workflow_dispatch.

Jobs:

- Dependency Review: Analyze dependency manifest changes in PRs for known vulnerabilities.
- SAST Scan: Run static application security testing on backend and frontend codebases.
- Secret Scanning: Verify no secrets or credentials are present in repository code, configuration files, or Dockerfiles.
- Container Scanning: Scan built Docker images for known CVEs in base images and installed packages.
- Dependency Audit: Run package manager audit commands for both backend and frontend dependencies.

## 2.4 deploy.yml (Optional, Future Stage)

Trigger events: workflow_dispatch only, or push to main after ci.yml and docker-push.yml succeed.

Jobs:

- Deploy to Staging: Pull latest images and update docker-compose services on staging infrastructure.
- Deploy to Production: Execute blue-green or rolling deployment strategy on production infrastructure.
- Health Verification: Run smoke tests against deployed application endpoints.

Deploy workflow is scoped as a future stage and is not required for initial CI/CD implementation.

---

# 3 Required Files

- .github/workflows/ci.yml: CI pipeline for pull requests and feature and develop pushes.
- .github/workflows/docker-push.yml: Docker build and push pipeline for main, develop, and tags.
- .github/workflows/security.yml: Scheduled and event-driven security scanning pipeline.
- .github/dependabot.yml: Automated dependency update configuration for GitHub Actions, Python, Node.js, and Docker base images.
- .dockerignore: Repository root dockerignore to exclude .env, .git, node_modules, dist, backend-logs, pytest cache, and IDE directories from Docker build context.
- backend/.dockerignore: Backend-specific dockerignore for .venv, __pycache__, .pytest_cache, .coverage, htmlcov, alembic versions, backend-logs, and local configuration files.
- frontend/.dockerignore: Frontend-specific dockerignore for node_modules, dist, .env, .vite, and build artifacts.
- backend/pyproject.toml or ruff.toml: Linter and formatter configuration for backend Python code.
- frontend/eslint.config.js or .eslintrc: Linter configuration for frontend code.
- frontend/vitest.config.ts: Test framework configuration for frontend unit and integration tests.
- docs/CI_CD_RUNBOOK.md: Operational runbook covering workflow descriptions, rerun procedures, common failure modes, escalation paths, and secrets rotation procedures.
- docs/GITHUB_REPOSITORY_SECRETS.md: Documentation of required GitHub repository secrets, their purposes, which workflows use them, and rotation recommendations.

---

# 4 Implementation Tasks

## 4.1 Repository Structure Setup

- Create .github/ directory at repository root.
- Create .github/workflows/ subdirectory.
- Add .dockerignore at repository root.
- Add backend/.dockerignore and frontend/.dockerignore.
- Add .github/dependabot.yml.

## 4.2 Backend Tooling

- Add ruff or flake8 and mypy configuration to backend if not already present.
- Document backend test invocation: pytest backend/tests.
- Verify pytest configuration supports asyncio test patterns.
- Ensure backend tests do not require live service connections or provide appropriate mocks and fixtures.

## 4.3 Frontend Tooling

- Add test framework dependency to frontend/package.json (Vitest recommended for Vite compatibility).
- Add lint script and lint devDependency to frontend/package.json (ESLint recommended).
- Add test script to frontend/package.json.
- Create vitest.config.ts if not present.
- Ensure test setup initializes test environment matching application configuration.

## 4.4 CI Pipeline Implementation

- Define ci.yml with jobs for backend lint, backend test, frontend lint, frontend type check, frontend build, frontend test, security scan, and docker build.
- Configure job dependencies using needs to optimize workflow execution time.
- Set up caching for Python pip packages and Node.js dependencies across jobs.
- Configure matrix strategy for Python and Node.js versions if multiple versions are supported.
- Add concurrency groups to cancel redundant workflow runs on the same branch.

## 4.5 Docker Push Pipeline Implementation

- Define docker-push.yml triggered on main, develop, and tags.
- Configure registry authentication using GitHub Actions environment.
- Implement image tagging strategy: sha-<commit>, branch-<name>, version-<semver>.
- Build and push images for backend, frontend, telegram-bot, and nginx.

## 4.6 Security Pipeline Implementation

- Define security.yml with scheduled weekly trigger and PR-based triggers.
- Integrate dependency vulnerability scanning tools.
- Configure secret scanning to fail on detected credentials.
- Set up container image scanning for built Docker images.

## 4.7 Documentation

- Create docs/CI_CD_RUNBOOK.md with operational procedures.
- Create docs/GITHUB_REPOSITORY_SECRETS.md with secrets inventory and usage mapping.
- Update .gitignore if new tool caches or artifacts are introduced by CI tools.

---

# 5 Acceptance Criteria

- ci.yml workflow exists and triggers on pull_request, feature/\*, and develop pushes without errors.
- ci.yml backend lint job runs configured linter and reports results to the PR.
- ci.yml backend test job executes full backend test suite and reports pass or fail status.
- ci.yml frontend build job completes successfully producing a production build artifact.
- ci.yml frontend lint and type check jobs run after lint and type check tooling is added to frontend package configuration.
- ci.yml frontend test job runs after test framework and dependencies are added to frontend package.json.
- ci.yml security scan job completes and reports findings without false positive failures on baseline dependencies.
- ci.yml docker build job builds all service Dockerfiles (backend, frontend, telegram-bot, nginx) successfully.
- docker-push.yml workflow exists and triggers on main, develop, and tag pushes.
- docker-push.yml builds and pushes Docker images with appropriate tags to the configured registry.
- security.yml workflow runs on schedule and on pull requests targeting main and develop.
- security.yml dependency review job analyzes PR manifests for known vulnerabilities.
- .github/dependabot.yml is configured and active for GitHub Actions, Python, Node.js, and Docker updates.
- No secrets, credentials, API keys, tokens, or passwords are hardcoded in any workflow file or configuration.
- Workflow artifacts are uploaded and retained for a defined period for debugging purposes.
- Branch protection rules for main and develop require ci.yml status checks to pass before merging.
- All required files listed in Section 3 are present in the repository.

---

# 6 References

- Documentation 10_DEPLOYMENT_ARCHITECTURE.md: Pipeline section referencing GitHub Actions with Push -> Tests -> Build -> Deploy.
- Documentation 15_OBSERVABILITY_ROADMAP.md: Monitoring stack and Docker Compose service definitions.
- docker-compose.yml: Service definitions for postgres, redis, backend, celery, scheduler, frontend, telegram-bot, nginx.
- backend/requirements.txt: Python dependency list including pytest and pytest-asyncio.
- frontend/package.json: Script definitions showing absence of test and lint scripts.
- .gitignore: Exclusion patterns for development artifacts.
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Dependabot Documentation: https://docs.github.com/en/code-security/dependabot
- Ruff Documentation: https://docs.astral.sh/ruff/
- Vitest Documentation: https://vitest.dev/
- ESLint Documentation: https://eslint.org/docs/latest/
