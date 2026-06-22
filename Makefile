.PHONY: help install dev test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	cd backend && poetry install
	cd frontend && npm install

dev: ## Start development environment
	docker compose -f docker-compose.dev.yml up -d

test: ## Run tests
	cd backend && pytest tests/ -v

lint: ## Run linters
	cd backend && ruff check src/
	cd frontend && npm run lint

format: ## Format code
	cd backend && ruff format src/
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

clean: ## Clean build artifacts
	cd backend && rm -rf dist build .pytest_cache htmlcov
	cd frontend && rm -rf dist node_modules/.vite

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create new migration
	cd backend && alembic revision --autogenerate -m "$(name)"
