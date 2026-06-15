#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
while [[ ! -f "$ROOT_DIR/docker-compose.yml" && "$ROOT_DIR" != "/" ]]; do
  ROOT_DIR="$(dirname "$ROOT_DIR")"
done

if [[ ! -f "$ROOT_DIR/docker-compose.yml" ]]; then
  echo "Unable to locate project root containing docker-compose.yml"
  exit 1
fi

cd "$ROOT_DIR"

echo "== Docker Compose config =="
docker compose config >/dev/null

if docker info >/dev/null 2>&1; then
  echo "== Docker daemon available; building backend and Telegram bot =="
  docker compose build backend telegram-bot
else
  echo "== Docker daemon unavailable; running local validation fallback =="
  echo "   - docker compose config: OK"
  echo "   - backend tests: running"
  (cd backend && pytest -q)
  echo "   - Python compile: running"
  python -m compileall backend telegram-bot
  echo "   - Alembic offline SQL: running"
  (cd backend && alembic upgrade head --sql >/dev/null)
  echo ""
  echo "Validation completed without Docker daemon. Start Docker Desktop and run:"
  echo "  docker compose build backend telegram-bot"
fi
