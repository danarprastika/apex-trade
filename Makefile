.PHONY: help install test lint format clean docker-up docker-down migrate backup restore

help:
	@echo "QuantX AI Makefile"
	@echo "  install          - Install all dependencies"
	@echo "  test             - Run test suite"
	@echo "  lint             - Run linters"
	@echo "  format           - Format code"
	@echo "  clean            - Clean build artifacts"
	@echo "  docker-up        - Start all services"
	@echo "  docker-down      - Stop all services"
	@echo "  migrate          - Run database migrations"
	@echo "  backup           - Backup database"
	@echo "  restore          - Restore database"

install:
	cd backend && pip install -e .
	cd frontend && npm install
	cd telegram && pip install -e .

test:
	cd backend && pytest tests/ -v
	cd frontend && npm test
	cd telegram && pytest tests/ -v

lint:
	cd backend && ruff check .
	cd frontend && npm run lint
	cd telegram && ruff check .

format:
	cd backend && ruff format .
	cd frontend && npm run format
	cd telegram && ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	cd backend && rm -rf .pytest_cache .ruff_cache .mypy_cache
	cd frontend && rm -rf node_modules dist build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

backup:
	@echo "Backing up database..."
	docker exec quantx-postgres pg_dump -U quantx quantx > backups/$(shell date +%Y%m%d_%H%M%S).sql

restore:
	@echo "Restoring database..."
	docker exec -i quantx-postgres psql -U quantx quantx < $(FILE)

.DEFAULT_GOAL := help
