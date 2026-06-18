#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENV_FILE="${ENV_FILE:-${PROJECT_ROOT}/.env}"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_FILE="${BACKUP_DIR}/apex_backup_${TIMESTAMP}.dump.gz"
TMP_BACKUP_FILE="${BACKUP_FILE}.tmp"

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

load_dotenv "$ENV_FILE"

POSTGRES_USER="${POSTGRES_USER:-apex}"
POSTGRES_DB="${POSTGRES_DB:-apex_db}"
PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD:-}}"
export PGPASSWORD

if [ -z "$PGPASSWORD" ]; then
  log "ERROR: PGPASSWORD or POSTGRES_PASSWORD is required"
  exit 1
fi

mkdir -p "$BACKUP_DIR"

log "Starting PostgreSQL backup for database=${POSTGRES_DB} user=${POSTGRES_USER} target=${BACKUP_FILE}"

set +e
compose exec -T -e "PGPASSWORD=${PGPASSWORD}" postgres pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip -c > "$TMP_BACKUP_FILE"
dump_status=$?
set -e

if [ "$dump_status" -ne 0 ]; then
  rm -f "$TMP_BACKUP_FILE"
  log "ERROR: pg_dump failed with exit code ${dump_status}"
  exit "$dump_status"
fi

mv "$TMP_BACKUP_FILE" "$BACKUP_FILE"
log "Backup completed: ${BACKUP_FILE}"

log "Removing backups older than ${RETENTION_DAYS} days from ${BACKUP_DIR}"
if ! find "$BACKUP_DIR" -maxdepth 1 -type f -name 'apex_backup_*.dump.gz' -mtime +"${RETENTION_DAYS}" -delete; then
  log "ERROR: backup retention cleanup failed"
  exit 1
fi

log "PostgreSQL backup finished successfully"
