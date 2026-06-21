# Package Dependency Rules

## Strict Dependency Flow

Presentation -> Application -> Domain <- Infrastructure

## Allowed Dependencies Per Layer

| From Layer | To Layer | Allowed | Notes |
|------------|----------|---------|-------|
| Presentation | Application | Yes | Via Use Case interfaces, DTOs |
| Presentation | Domain | No | Must go through Application layer |
| Application | Domain | Yes | Primary dependency direction |
| Application | Infrastructure | No | Inversion of control required |
| Infrastructure | Domain | Yes | Implements interfaces only |
| Infrastructure | Application | No | Wrong direction; creates coupling |
| Infrastructure | Presentation | No | Wrong direction; creates coupling |

## Forbidden Dependencies

### Domain Layer
- Cannot import from Application, Infrastructure, or Presentation
- Cannot depend on external libraries (standard library only)
- Cannot reference concrete implementations

### Application Layer
- Cannot import from Infrastructure or Presentation
- Cannot use database clients, HTTP clients, or external SDKs
- Must depend only on Domain interfaces

### Infrastructure Layer
- Cannot import from Presentation
- Can only import from Domain (interfaces)
- Should not depend on Application layer

### Presentation Layer
- Cannot import from Infrastructure
- Can only import from Application (interfaces)
- Must use DTOs, not Domain entities

## Circular Dependency Prevention

### Strategies
1. Dependency Injection: Inject dependencies via constructor
2. Interfaces in Domain: Define contracts in Domain, implement in Infrastructure
3. Event-Driven Communication: Publish events instead of direct calls
4. Mediator Pattern: Use mediator for cross-module communication
5. Shared Kernel: Keep common types in a shared kernel

### Detection
- CI pipeline runs import-linter or similar
- Pre-commit hook checks for circular imports
- Modular architecture review per sprint

## Internal Module Dependency Rules

### Within Domain
- Entities can reference other entities
- Entities can use value objects
- Domain services can use repositories (interfaces)
- No circular dependencies between aggregates

### Within Application
- Use Cases depend on Domain entities and services
- Command/Query handlers depend on Use Cases
- DTOs are independent data structures

### Within Infrastructure
- Repositories implement Domain interfaces
- Adapters implement Domain interfaces
- Database models map to Domain entities

### Within Presentation
- Controllers depend on Application Use Cases
- DTOs separate from Domain entities
- No business logic in controllers

## External Dependency Policy

### Versioning
- All dependencies pinned to exact versions
- Regular security updates via Dependabot
- Major version updates require ADR

### Selection Criteria
- Actively maintained (commits in last 6 months)
- Type hints for Python libraries
- Reasonable API surface area
- Good documentation
- Permissive license (MIT, Apache, BSD)

### Prohibited Dependencies in Domain
- No database drivers (SQLAlchemy, asyncpg)
- No HTTP clients (httpx, requests)
- No external SDKs (CCXT, aiogram)
- No framework dependencies (FastAPI, SQLAlchemy)

### Permitted in Domain
- Standard library (datetime, decimal, enum, dataclasses)
- Pydantic for validation
- Typing extensions
