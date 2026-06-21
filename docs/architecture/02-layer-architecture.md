# Layer Architecture

## Clean Architecture Layers

The QuantX AI platform implements Clean Architecture with four concentric layers.

### Layer Overview

```
+------------------------------------------------------------------+
|                        PRESENTATION LAYER                          |
|  React Dashboard     |   Telegram Bot    |   WebSocket API          |
+----------------------+--------------------+-------------------------+
                              |
+------------------------------------------------------------------+
|                      APPLICATION LAYER                             |
|  Use Cases           |   Services        |   Command Handlers      |
|  DTOs                |   Application     |   Event Handlers        |
|  Request/Response    |   Services        |                          |
+----------------------+--------------------+-------------------------+
                              |
+------------------------------------------------------------------+
|                         DOMAIN LAYER                               |
|  Entities            |   Value Objects     |   Domain Services     |
|  Aggregates          |   Domain Events     |   Repository          |
|  Domain Exceptions   |   Business Rules    |   Interfaces          |
+----------------------+--------------------+-------------------------+
                              ^
+------------------------------------------------------------------+
|                     INFRASTRUCTURE LAYER                           |
|  Database Adapters   |   Cache Adapters  |   Exchange Adapters   |
|  External Services   |   Message Queue   |   Email/SMS Gateways    |
|  Repository Impls    |   AI Providers    |   Telegram Gateways   |
+------------------------------------------------------------------+
```

### Layer Responsibilities

| Layer | Responsibility | Technology | Primary Concerns |
|-------|---------------|------------|----------------|
| Presentation | User interface, bot interactions, API endpoints | React, FastAPI, aiogram | HTTP handling, UI rendering, request/response |
| Application | Use cases, orchestration, business logic coordination | Python Services, Use Cases | Workflow management, transaction coordination |
| Domain | Core business logic, entities, rules | Pure Python | Trading rules, money calculations, risk limits |
| Infrastructure | External integrations, persistence, messaging | PostgreSQL, Redis, CCXT, Gemini API | Database access, API calls, caching, messaging |

## Layer Boundaries

### Domain Layer
- Entities: TradingAccount, Portfolio, Position, Order, Strategy, MarketData
- Value Objects: Symbol, Price, Quantity, Money, Timestamp
- Domain Services: TradingEngine, RiskEvaluator, PortfolioCalculator
- Repository Interfaces: Abstract definitions
- **Cannot import from outer layers**

### Application Layer
- Use Cases: ExecuteTrade, CalculatePortfolio, GenerateStrategy
- Application Services: MarketDataService, NotificationService
- Command/Query Handlers: PlaceOrder, CreateStrategy
- DTOs: Request/Response objects
- **Can only depend on Domain layer**

### Infrastructure Layer
- Database Adapters: SQLAlchemy implementations
- Cache Adapters: Redis implementations
- Exchange Adapters: CCXT wrappers
- AI Adapters: Gemini, OpenRouter clients
- **Can depend on Domain (interfaces)**

### Presentation Layer
- REST Controllers: FastAPI handlers
- WebSocket Handlers: Real-time streams
- Bot Controllers: Telegram handlers
- **Consumes Application services**

## Dependency Direction Rules

Dependencies flow only inward: Presentation -> Application -> Domain <- Infrastructure

```
+------------------------------------------------------------------+
|                    INFRASTRUCTURE LAYER                           |
|  [Depends on Domain interfaces]                                   |
+------------------------------------------------------------------+
                              ^
+------------------------------------------------------------------+
|                         DOMAIN LAYER                               |
|  [Zero external dependencies]                                     |
+------------------------------------------------------------------+
                              ^
+------------------------------------------------------------------+
|                      APPLICATION LAYER                             |
|  [Depends on Domain]                                               |
+------------------------------------------------------------------+
                              ^
+------------------------------------------------------------------+
|                        PRESENTATION LAYER                          |
|  [Depends on Application]                                          |
+------------------------------------------------------------------+
```

## Cross-Cutting Concerns Placement

| Concern | Placement | Rationale |
|---------|-----------|-----------|
| Logging | Infrastructure (technical), Application (business) | Technical logging at infrastructure, business events at application |
| Authentication | Presentation Layer | Request-level concern |
| Validation | Presentation (input), Domain (business rules) | Input vs business validation |
| Caching | Infrastructure implementation, Application strategy | Technical cache vs cache policy |
| Authorization | Presentation Layer | Security boundary |
| Error Handling | Each layer, with domain exceptions | Domain errors bubble, infrastructure wrapped |
| Monitoring | Infrastructure layer | Telemetry collection |
