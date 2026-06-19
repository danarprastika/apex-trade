# APEX Financial Intelligence Platform

Version: 0.1
Status: Draft
Document Type: Backend Architecture

---

# 1. Backend Goals

Backend bertanggung jawab untuk:

- Authentication
- Authorization
- Market Data Collection
- Trading Engine
- Risk Management
- Portfolio Management
- Telegram Integration
- Web Dashboard API
- Monitoring
- Audit Logging

Backend harus:

- Modular
- Testable
- Scalable
- Secure
- AI Ready

---

# 2. Technology Stack

Framework:
FastAPI

Language:
Python 3.12+

ORM:
SQLAlchemy 2.x

Validation:
Pydantic v2

Database:
PostgreSQL

Migration:
Alembic

Authentication:
JWT

Password Hash:
bcrypt

Cache:
Redis

Task Scheduler:
APScheduler

HTTP Client:
httpx

Exchange SDK:
CCXT

Testing:
pytest

Logging:
structlog

---

# 3. Architectural Style

Pattern:

Modular Monolith

Layers:

Presentation Layer
Application Layer
Domain Layer
Infrastructure Layer

---

# 4. Project Structure

backend/

├── app/
│
├── api/
│   ├── auth/
│   ├── users/
│   ├── exchanges/
│   ├── market/
│   ├── trading/
│   ├── portfolio/
│   ├── risk/
│   ├── notifications/
│   ├── admin/
│   └── health/
│
├── core/
│   ├── config/
│   ├── security/
│   ├── logging/
│   ├── exceptions/
│   └── constants/
│
├── database/
│   ├── models/
│   ├── repositories/
│   ├── session.py
│   └── base.py
│
├── services/
│   ├── auth/
│   ├── exchange/
│   ├── market/
│   ├── strategy/
│   ├── signal/
│   ├── execution/
│   ├── risk/
│   ├── portfolio/
│   ├── notification/
│   └── audit/
│
├── tasks/
│   ├── collectors/
│   ├── schedulers/
│   └── workers/
│
├── schemas/
│
├── events/
│
├── integrations/
│   ├── binance/
│   ├── telegram/
│   └── redis/
│
├── tests/
│
└── main.py

---

# 5. API Design Standards

Base URL

/api/v1

Examples

/api/v1/auth/login

/api/v1/users

/api/v1/portfolio

/api/v1/trades

---

Response Format

{
  "success": true,
  "message": "Request successful",
  "data": {}
}

---

Error Format

{
  "success": false,
  "message": "Validation error",
  "errors": []
}

---

# 6. Authentication Module

Endpoints

POST /auth/register

POST /auth/login

POST /auth/refresh

POST /auth/logout

GET /auth/me

---

JWT Structure

Access Token:
15 minutes

Refresh Token:
7 days

---

Roles

SUPER_ADMIN

ADMIN

TRADER

VIEWER

---

# 7. User Module

Endpoints

GET /users

GET /users/{id}

PUT /users/{id}

DELETE /users/{id}

GET /users/settings

PUT /users/settings

---

# 8. Exchange Module

Endpoints

GET /exchanges

POST /exchange-accounts

GET /exchange-accounts

PUT /exchange-accounts/{id}

DELETE /exchange-accounts/{id}

POST /exchange-accounts/test

---

# 9. Market Module

Endpoints

GET /market/assets

GET /market/pairs

GET /market/candles

GET /market/orderbook

GET /market/funding

GET /market/open-interest

---

# 10. Strategy Module

Endpoints

GET /strategies

POST /strategies

PUT /strategies/{id}

DELETE /strategies/{id}

---

# 11. Signal Module

Endpoints

GET /signals

GET /signals/{id}

GET /signals/latest

---

# 12. Trading Module

Endpoints

GET /orders

POST /orders

GET /positions

GET /trades

GET /trades/{id}

---

# 13. Portfolio Module

Endpoints

GET /portfolio

GET /portfolio/snapshots

GET /portfolio/allocation

---

# 14. Risk Module

Endpoints

GET /risk/profile

PUT /risk/profile

GET /risk/events

---

# 15. Notification Module

Endpoints

GET /notifications

PUT /notifications/{id}/read

---

# 16. Monitoring Module

Endpoints

GET /health

GET /metrics

GET /system-alerts

---

# 17. Service Layer

Rule:

Controllers never access database directly.

Flow:

API
↓
Service
↓
Repository
↓
Database

---

Example

TradeController
↓
TradeService
↓
TradeRepository
↓
PostgreSQL

---

# 18. Repository Pattern

Purpose:

Memisahkan business logic dan database logic.

Example

UserRepository

TradeRepository

PortfolioRepository

SignalRepository

---

# 19. Background Jobs

Collector Jobs

Market Collector

Portfolio Sync

Exchange Sync

---

Scheduler Jobs

1 Minute

5 Minute

15 Minute

1 Hour

Daily

---

# 20. Event System

Events

MarketUpdated

SignalGenerated

TradeOpened

TradeClosed

RiskTriggered

NotificationRequested

---

Flow

Event
↓
Event Handler
↓
Service Action

---

# 21. Security Standards

Passwords

bcrypt

---

API Keys

AES Encryption

---

JWT

Signed Secret

---

Rate Limiting

Enabled

---

CORS

Restricted

---

# 22. Logging Standards

Levels

DEBUG

INFO

WARNING

ERROR

CRITICAL

---

Every Log Must Include

timestamp

module

user_id

event_type

message

---

# 23. Error Handling

Global Exception Handler

Validation Error Handler

Database Error Handler

Exchange Error Handler

---

# 24. Testing Strategy

Unit Tests

Repository Tests

Service Tests

API Tests

Integration Tests

---

Target Coverage

80%+

---

# 25. MVP Scope

Must Implement

Authentication

Users

Exchange Accounts

Market Collector

Strategy Engine

Signal Engine

Risk Engine

Portfolio

Telegram Notifications

Monitoring

Audit Logs

---

# End Document