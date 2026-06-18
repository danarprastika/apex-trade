#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${ENV_FILE:-${PROJECT_ROOT}/.env}"
BACKUP_FILE="${1:-}"
TARGET_DB="${RESTORE_DB:-}"
DROP_DATABASE="${DROP_DATABASE:-true}"

load_dotenv() {
  local env_file="$1"
  local line key value

  [ -f "$env_file" ] || return 0

  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]] || continue

    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"

    export "$key=$value"
  done < "$env_file"
}

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

compose() {
  docker compose -f "${PROJECT_ROOT}/docker-compose.yml" "$@"
}

usage() {
  printf 'Usage: %s <backup-file.dump.gz>\n' "$0"
  printf 'WARNING: By default this script drops and recreates the target database, overwriting existing data.\n'
  printf 'Set RESTORE_DB=<database> and DROP_DATABASE=false to restore into a dedicated database without dropping it.\n'
}

load_dotenv "$ENV_FILE"

if [ -z "$BACKUP_FILE" ]; then
  usage
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  log "ERROR: backup file not found: ${BACKUP_FILE}"
  exit 1
fi

BACKUP_FILE="$(cd "$(dirname "$BACKUP_FILE")" && pwd)/$(basename "$BACKUP_FILE")"
POSTGRES_USER="${POSTGRES_USER:-apex}"
POSTGRES_DB="${POSTGRES_DB:-apex_db}"
TARGET_DB="${TARGET_DB:-$POSTGRES_DB}"
PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD:-}}"
export PGPASSWORD

if [ -z "$PGPASSWORD" ]; then
  log "ERROR: PGPASSWORD or POSTGRES_PASSWORD is required"
  exit 1
fi

log "WARNING: Restore will overwrite existing data in database=${TARGET_DB}"
log "Starting PostgreSQL restore from ${BACKUP_FILE}"

if [ "$DROP_DATABASE" = "true" ]; then
  log "Dropping and recreating database=${TARGET_DB}"
  compose exec -T -e "PGPASSWORD=${PGPASSWORD}" postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -v target_db="$TARGET_DB" <<'SQL'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = :'target_db'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS :"target_db";
CREATE DATABASE :"target_db";
SQL
else
  log "Creating database=${TARGET_DB} if it does not exist"
  compose exec -T -e "PGPASSWORD=${PGPASSWORD}" postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -v target_db="$TARGET_DB" <<'SQL'
SELECT format('CREATE DATABASE %I', :'target_db')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'target_db')\gexec
SQL
fi

set +e
gzip -dc "$BACKUP_FILE" | compose exec -T -e "PGPASSWORD=${PGPASSWORD}" postgres pg_restore -U "$POSTGRES_USER" -d "$TARGET_DB" --clean --if-exists --exit-on-error
restore_status=$?
set -e

if [ "$restore_status" -ne 0 ]; then
  log "ERROR: pg_restore failed with exit code ${restore_status}"
  exit "$restore_status"
fi

log "Validating restore with simple query"
compose exec -T -e "PGPASSWORD=${PGPASSWORD}" postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$TARGET_DB" -c 'SELECT 1 AS restore_validation;'

log "PostgreSQL restore finished successfully"
