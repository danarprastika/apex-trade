# 12_REPOSITORY_BOOTSTRAP.md

# APEX Financial Intelligence Platform

Version: 0.1
Status: Approved
Document Type: Repository Bootstrap

---

# 1. Purpose

Dokumen ini mendefinisikan fondasi repository yang siap digunakan untuk pengembangan APEX.

Setelah bootstrap selesai, developer dapat langsung menjalankan:

* FastAPI
* PostgreSQL
* Redis
* Telegram Bot
* React Frontend

menggunakan Docker Compose.

---

# 2. Repository Structure

apex/

├── backend/
├── frontend/
├── telegram-bot/
├── infrastructure/
├── docker/
├── docs/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
└── LICENSE

---

# 3. Environment Variables

.env.example

APP_NAME=APEX

APP_ENV=development

DEBUG=true

API_HOST=0.0.0.0

API_PORT=8000

POSTGRES_USER=apex

POSTGRES_PASSWORD=apex_password

POSTGRES_DB=apex_db

POSTGRES_HOST=postgres

POSTGRES_PORT=5432

REDIS_HOST=redis

REDIS_PORT=6379

JWT_SECRET_KEY=CHANGE_THIS_SECRET

JWT_ALGORITHM=HS256

JWT_EXPIRE_MINUTES=15

TELEGRAM_BOT_TOKEN=

BINANCE_API_KEY=

BINANCE_API_SECRET=

---

# 4. Git Ignore

Python

**pycache**/

*.pyc

venv/

.venv/

Logs

logs/

*.log

Environment

.env

.env.*

Node

node_modules/

dist/

build/

IDE

.vscode/

.idea/

---

# 5. Docker Compose

version: "3.9"

services:

postgres:

image: postgres:16

container_name: apex-postgres

restart: always

environment:

POSTGRES_USER: apex

POSTGRES_PASSWORD: apex_password

POSTGRES_DB: apex_db

ports:

* "5432:5432"

volumes:

* postgres-data:/var/lib/postgresql/data

redis:

image: redis:7

container_name: apex-redis

restart: always

ports:

* "6379:6379"

backend:

build:

context: ./backend

dockerfile: Dockerfile

container_name: apex-backend

restart: always

depends_on:

* postgres

* redis

ports:

* "8000:8000"

frontend:

build:

context: ./frontend

dockerfile: Dockerfile

container_name: apex-frontend

restart: always

ports:

* "3000:80"

telegram-bot:

build:

context: ./telegram-bot

dockerfile: Dockerfile

container_name: apex-telegram

restart: always

depends_on:

* backend

volumes:

postgres-data:

---

# 6. Backend Structure

backend/

├── api/
│ ├── auth/
│ ├── users/
│ ├── exchanges/
│ ├── market/
│ ├── trading/
│ ├── portfolio/
│ ├── risk/
│ ├── notifications/
│ └── health/

├── core/
│ ├── config/
│ ├── security/
│ ├── logging/
│ ├── exceptions/
│ └── dependencies/

├── database/
│ ├── models/
│ ├── repositories/
│ ├── migrations/
│ ├── base.py
│ └── session.py

├── schemas/

├── services/

├── tasks/

├── integrations/

├── tests/

├── requirements.txt

└── main.py

---

# 7. Backend Requirements

fastapi

uvicorn[standard]

sqlalchemy

psycopg2-binary

alembic

pydantic

pydantic-settings

python-jose

passlib[bcrypt]

redis

httpx

ccxt

apscheduler

structlog

pytest

pytest-asyncio

---

# 8. FastAPI Starter

main.py

FastAPI Application

Endpoints:

GET /

GET /health

Response:

{
"status": "healthy"
}

---

# 9. Database Bootstrap

Database Engine:

PostgreSQL 16

ORM:

SQLAlchemy 2.x

Migration:

Alembic

Initial Tables:

users

user_settings

---

# 10. Redis Bootstrap

Purpose:

Cache

Sessions

Rate Limiting

Notification Queue

Background Jobs

---

# 11. Telegram Bootstrap

Structure:

telegram-bot/

├── bot.py

├── handlers/

├── keyboards/

├── middlewares/

├── services/

└── requirements.txt

Features:

/start

/help

/status

/portfolio

/signals

---

# 12. Frontend Bootstrap

Technology:

React

TypeScript

Vite

Tailwind CSS

Structure:

frontend/

├── src/

├── pages/

├── components/

├── layouts/

├── services/

├── hooks/

├── store/

└── router/

---

# 13. Docker Images

backend

python:3.12-slim

frontend

node:22-alpine

telegram-bot

python:3.12-slim

postgres

postgres:16

redis

redis:7

---

# 14. Health Checks

Backend

GET /health

Database

Connection Test

Redis

Ping

Telegram

Bot Status

---

# 15. MVP Success Criteria

docker compose up

Successfully starts:

✅ PostgreSQL

✅ Redis

✅ FastAPI

✅ React

✅ Telegram Bot

Health endpoint:

http://localhost:8000/health

returns:

{
"status": "healthy"
}

---

# 16. Sprint Roadmap

Sprint 1

Authentication

Users

JWT

Alembic

Sprint 2

Exchange Integration

Market Collector

Candles

Sprint 3

Strategy Engine

Signal Engine

Paper Trading

Sprint 4

Telegram

Portfolio

Notifications

Sprint 5

Risk Engine

Monitoring

Analytics

Sprint 6

Backtesting

News Intelligence

Sentiment Intelligence

Sprint 7

Prediction Engine

Machine Learning

Sprint 8

Multi-Agent Intelligence

Knowledge Graph

Financial Memory

---

# End Document
