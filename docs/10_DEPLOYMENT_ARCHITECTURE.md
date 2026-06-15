# APEX Financial Intelligence Platform

Version: 0.1
Status: Draft
Document Type: Deployment Architecture

---

# 1. Purpose

Dokumen ini mendefinisikan:

- Infrastruktur Development
- Infrastruktur Staging
- Infrastruktur Production
- Monitoring
- Backup
- Security
- Scaling Strategy

---

# 2. Infrastructure Philosophy

Build Small
Scale Gradually

Rules:

1. One Server First
2. Docker Everywhere
3. Infrastructure As Code
4. Automate Everything
5. Monitor Everything

---

# 3. Environment Stages

Development

Local Machine

---

Staging

Optional

Single VPS

---

Production

Single VPS

---

Future

Multi Server Cluster

---

##################################################
# STAGE 1
# MVP INFRASTRUCTURE
##################################################

Target Budget

Rp 50.000 – Rp 150.000 / bulan

---

Components

FastAPI

PostgreSQL

Redis

Telegram Bot

React Frontend

Nginx

Docker

---

Deployment Layout

┌─────────────────────┐
│ Ubuntu VPS          │
│                     │
│ FastAPI             │
│ PostgreSQL          │
│ Redis               │
│ Telegram Bot        │
│ React Build         │
│ Nginx               │
└─────────────────────┘

---

Recommended Specs

CPU

2 vCPU

RAM

2 GB

Storage

30 GB SSD

---

##################################################
# CONTAINER ARCHITECTURE
##################################################

docker-compose

Services:

backend

frontend

postgres

redis

telegram_bot

nginx

---

Network

apex-network

---

Volumes

postgres-data

redis-data

logs

backups

---

##################################################
# FASTAPI DEPLOYMENT
##################################################

Container

backend

Port

8000

---

Workers

2

---

Server

Uvicorn

Production

Gunicorn + Uvicorn Workers

---

Health Checks

/health

/metrics

---

##################################################
# POSTGRESQL DEPLOYMENT
##################################################

Container

postgres

---

Version

16+

---

Storage

Persistent Volume

---

Backups

Daily

---

Future

Read Replica

Partitioning

---

##################################################
# REDIS DEPLOYMENT
##################################################

Container

redis

---

Purposes

Cache

Sessions

Task Queue

Rate Limiting

Notification Queue

---

##################################################
# TELEGRAM BOT DEPLOYMENT
##################################################

Container

telegram-bot

---

Connection

Backend API

---

Recovery

Auto Restart

---

##################################################
# REACT DEPLOYMENT
##################################################

Container

frontend

---

Build Mode

Production Build

---

Served By

Nginx

---

##################################################
# NGINX DEPLOYMENT
##################################################

Responsibilities

SSL

Reverse Proxy

Load Balancing

Compression

Caching

---

Routes

/api → backend

/ → frontend

---

##################################################
# DOMAIN STRUCTURE
##################################################

Development

localhost

---

Production

app.domain.com

api.domain.com

---

Future

ai.domain.com

research.domain.com

---

##################################################
# SSL
##################################################

Provider

Let's Encrypt

---

Renewal

Automatic

---

##################################################
# MONITORING STACK
##################################################

Stage 1

Basic Monitoring

---

Metrics

CPU

RAM

Disk

API Status

Database Status

---

Stage 2

Prometheus

Grafana

Loki

---

Alerts

Telegram

Email

---

##################################################
# LOGGING
##################################################

Application Logs

Backend Logs

Bot Logs

Nginx Logs

Database Logs

---

Retention

30 Days

---

##################################################
# BACKUP STRATEGY
##################################################

Database Backup

Daily

---

Full Backup

Weekly

---

Archive Backup

Monthly

---

Storage

Local

Cloud Storage (Future)

---

##################################################
# SECURITY
##################################################

Authentication

JWT

---

Passwords

bcrypt

---

API Keys

Encrypted

---

Database

Private Network

---

Firewall

Enabled

---

Fail2Ban

Enabled

---

##################################################
# CI/CD PIPELINE
##################################################

Repository

GitHub

---

Branches

main

develop

feature/*

---

Pipeline

Push
↓
Tests
↓
Build
↓
Deploy

---

Tools

GitHub Actions

---

##################################################
# SCALING ROADMAP
##################################################

Phase 1

Single VPS

1-100 Users

---

Phase 2

Larger VPS

100-1000 Users

---

Phase 3

Separate Database

Separate Backend

1000-5000 Users

---

Phase 4

Multi Server

Load Balancer

5000+ Users

---

##################################################
# DISASTER RECOVERY
##################################################

RPO

24 Hours

---

RTO

2 Hours

---

Recovery Steps

Restore Backup

Restart Containers

Verify Data

Resume Services

---

##################################################
# COST OPTIMIZATION
##################################################

Stage 1

Single VPS

Open Source Tools

No Paid AI

No Managed Database

---

Stage 2

Optional Upgrades

More RAM

Dedicated Database

Prometheus Stack

---

Stage 3

Institutional Scale

Cluster Deployment

Managed Infrastructure

---

##################################################
# DEPLOYMENT PRINCIPLES
##################################################

1. Simplicity First

2. Security First

3. Automation First

4. Monitoring First

5. Cost Efficiency

6. Future Scalability

7. Zero Data Loss Priority

8. Docker Everywhere

9. Infrastructure As Code

10. Always Recoverable

---

# End Document