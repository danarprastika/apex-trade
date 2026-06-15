#!/usr/bin/env bash
set -euo pipefail

mkdir -p infrastructure/backups
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-apex}" "${POSTGRES_DB:-apex_db}" > "infrastructure/backups/apex-$(date +%Y%m%d-%H%M%S).sql"
