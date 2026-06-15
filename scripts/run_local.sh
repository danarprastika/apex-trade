#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not available. Start Docker Desktop or run scripts/validate_local.sh for daemon-free validation."
  exit 1
fi

docker compose up --build
