#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: ./scripts/restore.sh <backup.sql>"
  exit 1
fi

docker compose exec -T postgres psql -U "${POSTGRES_USER:-apex}" -d "${POSTGRES_DB:-apex_db}" < "$1"
