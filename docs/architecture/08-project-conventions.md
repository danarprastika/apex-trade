# Project Conventions

## Repository Pattern

### Interface Definition (Domain Layer)
- Abstract repository interfaces define data access contracts
- Located in domain/repositories/
- No implementation details

### Implementation (Infrastructure Layer)
- Concrete implementations in infrastructure/database/repositories/
- Implement domain interfaces
- Handle SQLAlchemy specifics, session management

### Generic Base Repository
- Common CRUD operations in base class
- Specific queries in specialized repositories
- Async methods for all operations

## Unit of Work

### Pattern Definition
- Single UoW per request/operation
- UoW coordinates multiple repository operations
- Commits on success, rollbacks on failure
- Database session managed by UoW

### Implementation Guidelines
- UoW exposes repositories as properties
- Domain services receive UoW, not repositories directly
- Context manager pattern for automatic cleanup

### Usage
- Passed through Application layer to Domain
- Ensures transaction consistency across multiple operations
- Handles commit/rollback automatically

## Dependency Injection

### Pattern
- Constructor injection preferred
- Interface injection for optional dependencies
- No service locator pattern

### Container Setup
- DI container configured in infrastructure layer
- All dependencies registered at startup
- Interfaces bound to implementations

### Example
- TradingEngine receives OrderRepository, PortfolioRepository, RiskEvaluator via constructor
- All dependencies are interfaces, not concrete classes

## Service Layer Conventions

### Application Services
- Orchestrate use cases
- Coordinate multiple domain services
- Handle transaction boundaries
- No business logic (delegate to domain)

### Domain Services
- Contain business logic
- No external dependencies
- Stateless operations
- Pure functions where possible

### Infrastructure Services
- Technical implementations
- External API clients
- Database operations
- Cache operations

## Domain Events

### Event Definition
- Dataclass with fields for event data
- Occurred_at timestamp
- Immutable after creation

### Event Publishing
- Events raised after state changes in domain
- Published through EventBus interface
- Handlers registered in Application layer
- No business logic in event handlers

### Event Naming
- Past tense: OrderPlaced, PositionUpdated, RiskTriggered
- Descriptive: includes entity type and action

## DTO vs Entity

### Entity (Domain Layer)
- Contains business behavior (methods)
- Enforces invariants
- Self-validating
- Never exposed directly through API

### DTO (Application/Presentation Layer)
- Data container only
- Used for API boundaries and serialization
- Can be flattened, denormalized views
- Maps to/from entities at layer boundaries

### Rules
- Never expose entities directly through API
- DTOs for serialization and API boundaries
- Map between DTO and Entity at layer boundaries
- DTOs can be flattened, denormalized views

## API Versioning

### Strategy
- URL path versioning: /api/v1/, /api/v2/
- Current version: v1
- Deprecation: 6-month notice before removal
- Version negotiation via Accept header optional

### Version Management
- New versions for breaking changes only
- Additive changes stay in same version
- Deprecation headers on old endpoints
- Migration guide in documentation
