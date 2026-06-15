# APEX Financial Intelligence Platform

Version: 0.1
Status: Approved
Document Type: Project Structure

---

# 1. Purpose

Dokumen ini mendefinisikan:

- Struktur repository
- Struktur backend
- Struktur frontend
- Struktur telegram bot
- Struktur infrastructure
- Standar organisasi source code

---

# 2. Repository Structure

apex/

├── backend/
├── frontend/
├── telegram-bot/
├── infrastructure/
├── docs/
├── scripts/
├── docker/
├── .github/
├── .env.example
├── docker-compose.yml
├── README.md
└── LICENSE

---

##################################################
# BACKEND
##################################################

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
│   ├── constants/
│   ├── exceptions/
│   └── dependencies/
│
├── database/
│   ├── base.py
│   ├── session.py
│   ├── models/
│   ├── repositories/
│   └── migrations/
│
├── schemas/
│
├── services/
│   ├── auth/
│   ├── users/
│   ├── exchange/
│   ├── market/
│   ├── strategy/
│   ├── signal/
│   ├── execution/
│   ├── portfolio/
│   ├── risk/
│   ├── notification/
│   └── audit/
│
├── integrations/
│   ├── binance/
│   ├── bybit/
│   ├── telegram/
│   └── redis/
│
├── events/
│
├── tasks/
│   ├── collectors/
│   ├── schedulers/
│   └── workers/
│
├── tests/
│
├── requirements.txt
│
└── main.py

---

##################################################
# FRONTEND
##################################################

frontend/

├── public/
│
├── src/
│
├── app/
│
├── pages/
│   ├── dashboard/
│   ├── market/
│   ├── trading/
│   ├── portfolio/
│   ├── analytics/
│   ├── settings/
│   └── admin/
│
├── components/
│
├── layouts/
│
├── hooks/
│
├── services/
│
├── store/
│
├── router/
│
├── types/
│
├── assets/
│
├── package.json
│
└── vite.config.ts

---

##################################################
# TELEGRAM BOT
##################################################

telegram-bot/

├── bot.py
│
├── handlers/
│   ├── start.py
│   ├── market.py
│   ├── trading.py
│   ├── portfolio.py
│   ├── settings.py
│   └── admin.py
│
├── keyboards/
│
├── middlewares/
│
├── services/
│
├── clients/
│
├── utils/
│
└── requirements.txt

---

##################################################
# INFRASTRUCTURE
##################################################

infrastructure/

├── nginx/
│
├── postgres/
│
├── redis/
│
├── monitoring/
│
└── backups/

---

##################################################
# DOCKER
##################################################

docker/

├── backend/
│   └── Dockerfile
│
├── frontend/
│   └── Dockerfile
│
├── telegram/
│   └── Dockerfile
│
└── nginx/
    └── Dockerfile

---

##################################################
# GITHUB ACTIONS
##################################################

.github/

└── workflows/

    ├── backend-ci.yml

    ├── frontend-ci.yml

    ├── deploy.yml

    └── tests.yml

---

##################################################
# DOCUMENTATION
##################################################

docs/

├── 01_PROJECT_VISION.md

├── 02_PRODUCT_REQUIREMENTS.md

├── 03_SYSTEM_ARCHITECTURE.md

├── 04_DOMAIN_MODEL.md

├── 04A_SYSTEM_BOUNDARIES.md

├── 05_DATABASE_ARCHITECTURE.md

├── 06_BACKEND_ARCHITECTURE.md

├── 07_TELEGRAM_ARCHITECTURE.md

├── 08_WEB_ARCHITECTURE.md

├── 09_AI_ARCHITECTURE.md

├── 10_DEPLOYMENT_ARCHITECTURE.md

├── 11_PROJECT_STRUCTURE.md

└── CHANGELOG.md

---

##################################################
# SCRIPTS
##################################################

scripts/

├── setup.sh

├── backup.sh

├── restore.sh

├── migrate.sh

├── seed_data.py

└── run_local.sh

---

##################################################
# ENVIRONMENT FILES
##################################################

.env

.env.development

.env.staging

.env.production

.env.example

---

##################################################
# BRANCH STRATEGY
##################################################

main

Production

---

develop

Development

---

feature/*

New Features

---

hotfix/*

Production Fixes

---

##################################################
# CODE STYLE
##################################################

Backend

black

ruff

isort

mypy

---

Frontend

eslint

prettier

---

##################################################
# TESTING STRUCTURE
##################################################

backend/tests/

├── unit/

├── integration/

└── api/

---

frontend/tests/

├── unit/

└── e2e/

---

##################################################
# MVP BUILD ORDER
##################################################

Phase 1

Authentication

Users

Database

---

Phase 2

Exchange Integration

Market Collector

Candles

---

Phase 3

Strategy Engine

Signals

Paper Trading

---

Phase 4

Telegram Bot

Notifications

Portfolio

---

Phase 5

Risk Engine

Monitoring

Analytics

---

Phase 6

Backtesting

News

Sentiment

---

Phase 7

AI Prediction

---

Phase 8

Multi-Agent System

---

# End Document