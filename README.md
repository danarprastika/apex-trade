# QuantX AI

AI-powered personal cryptocurrency trading platform.

## Architecture

Clean Architecture with four layers:
- Domain: Core business logic
- Application: Use cases and orchestration
- Infrastructure: External integrations
- Presentation: FastAPI API, Telegram bot, WebSocket

## Quick Start

```bash
cp .env.example .env
docker compose up -d
```

## Documentation

See [docs/architecture](docs/architecture) for full architecture documentation.
