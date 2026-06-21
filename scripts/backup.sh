#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec quantx-postgres pg_dump -U quantx quantx > "backups/quantx_${TIMESTAMP}.sql"
echo "Backup saved to backups/quantx_${TIMESTAMP}.sql"
