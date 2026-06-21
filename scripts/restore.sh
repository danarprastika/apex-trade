#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: ./restore.sh <backup-file>"
    exit 1
fi

docker exec -i quantx-postgres psql -U quantx quantx < "$1"
echo "Database restored from $1"
