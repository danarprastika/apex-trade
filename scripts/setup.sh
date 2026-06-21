#!/usr/bin/env bash
set -euo pipefail

echo "Setting up QuantX AI development environment..."

# Create environment files
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Start dependencies
docker compose up -d postgres redis

# Install backend
cd backend
pip install -e ".[dev]"

# Install frontend
cd ../frontend
npm install

# Install telegram
cd ../telegram
pip install -e ".[dev]"

echo "Setup complete. Run 'make docker-up' to start all services."
