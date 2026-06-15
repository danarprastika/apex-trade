#!/usr/bin/env bash
set -euo pipefail

cp .env.example .env
docker compose build
docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
docker compose up -d
