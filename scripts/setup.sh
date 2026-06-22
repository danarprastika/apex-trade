#!/bin/bash
# QuantX AI bootstrap script
set -e

echo "Bootstrapping QuantX AI development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting."; exit 1; }

# Start services
docker-compose up -d postgres redis

echo "Waiting for services to be ready..."
sleep 5

echo "Development environment ready."
echo "Run 'make dev' to start the application."
