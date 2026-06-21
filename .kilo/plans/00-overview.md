# QuantX AI - Project Architecture Overview

## Executive Summary

QuantX AI is a production-grade Personal AI Trading Platform designed for a **single user** running on a **Linux VPS**. This architecture document defines the complete blueprint for the system, establishing a single source of truth that all future development must follow.

## System Context

### Non-Negotiable Constraints
- **Single User Only**: No multi-tenancy, no SaaS, no public API
- **Platform**: Linux VPS (containerized deployment)
- **Architecture**: Clean Architecture + DDD + SOLID principles
- **Async-First**: Fully asynchronous throughout all layers
- **Security-First**: Enterprise-grade security patterns

### Primary Interfaces
1. **Telegram Bot** (aiogram 3.x) - Primary control interface
2. **Web Dashboard** (React + TypeScript) - Analytics and monitoring
3. **WebSocket** - Real-time market data streaming
4. **Direct API** - Programmatic access for automation

### Core Capabilities
- Multi-exchange trading via CCXT
- AI-powered market analysis (Gemini API + OpenRouter fallback)
- Real-time portfolio tracking
- Automated trading strategies
- Risk management engine
- Historical analysis and reporting

## Architectural Principles

### 1. Clean Architecture
Strict layer separation with dependencies pointing inward. No framework leakage across layers.

### 2. Domain-Driven Design
Rich domain models with explicit bounded contexts. Ubiquitous language throughout the codebase.

### 3. SOLID Principles
Every component designed with single responsibility and dependency inversion.

### 4. Async-First Design
All I/O operations are asynchronous. No blocking calls in the main application flow.

### 5. Security-First
Security embedded at every layer, not bolted on.

## High-Level Data Flow

```
External Data Sources (Exchanges, News, AI APIs)
    ↓
[Infrastructure Layer] (CCXT Clients, HTTP Clients, WebSocket Clients)
    ↓
[Application Layer] (Services, Orchestrators)
    ↓
[Domain Layer] (Business Logic, Aggregates, Value Objects)
    ↓
[Presentation Layer] (Controllers, WebSocket Handlers, Telegram Bot)
    ↓
User Interfaces (Telegram, Web UI, API)
```

## Key Architectural Decisions (Summary)

| Decision | Rationale |
|----------|-----------|
| FastAPI over Flask | Async-first, type safety, automatic documentation |
| PostgreSQL over NoSQL | ACID compliance for financial data, complex queries |
| Redis for caching | Session management, real-time data cache, pub/sub |
| AIOGram 3.x for Telegram | Native async, modern Python 3.12+ support |
| React + TypeScript | Type safety, ecosystem maturity, Vite performance |
| TanStack Query | Server-state management, caching, optimistic updates |
| TailwindCSS | Utility-first, production-ready, rapid UI development |
| Docker Compose for orchestration | Single VPS deployment, simplicity, reproducibility |
| GitHub Actions for CI/CD | Native GitHub integration, cost-effective |
| Alembic for migrations | SQLAlchemy native, reliable versioning |

## System Boundaries

### Inside the Circle (Core Domain)
- Trading strategies and execution
- Portfolio management
- Risk calculations
- Market analysis logic
- AI decision-making frameworks

### Outside the Circle (Infrastructure)
- CCXT exchange integrations
- AI API clients (Gemini, OpenRouter)
- Notification systems (Telegram, Email)
- Data persistence (PostgreSQL, Redis)
- File storage (logs, reports)

## Success Metrics

- **Latency**: Market data < 100ms, Order execution < 500ms
- **Uptime**: 99.9% platform availability
- **Accuracy**: Trade signal accuracy > 60%
- **Security**: Zero unauthorized access events
- **Maintainability**: Coverage > 80% tests, < 1 week MTTR

---

## Document Index

This architecture specification is divided into the following documents:

1. [Overall System Architecture](./01-overall-system-architecture.md)
2. [Layer Architecture](./02-layer-architecture.md)
3. [Folder Architecture](./03-folder-architecture.md)
4. [Module Architecture](./04-module-architecture.md)
5. [Package Dependency Rules](./05-package-dependency-rules.md)
6. [Folder Naming Rules](./06-folder-naming-rules.md)
7. [Coding Standards](./07-coding-standards.md)
8. [Project Conventions](./08-project-conventions.md)
9. [Logging Standards](./09-logging-standards.md)
10. [Error Handling Standards](./10-error-handling-standards.md)
11. [Configuration Standards](./11-configuration-standards.md)
12. [Security Standards](./12-security-standards.md)
13. [Environment Strategy](./13-environment-strategy.md)
14. [Testing Strategy](./14-testing-strategy.md)
15. [Deployment Strategy](./15-deployment-strategy.md)
16. [Roadmap](./16-roadmap.md)
17. [Sprint Breakdown](./17-sprint-breakdown.md)
18. [Future Extension Strategy](./18-future-extension-strategy.md)
19. [Definition of Done](./19-definition-of-done.md)
20. [Architecture Decision Summary](./20-architecture-decision-summary.md)
