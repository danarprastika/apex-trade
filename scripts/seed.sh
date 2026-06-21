#!/usr/bin/env bash
set -euo pipefail

echo "Seeding database..."
cd backend
python -m app.infra.db.seed
