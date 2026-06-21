# Configuration Standards

## Configuration Layering

### Layer 1: Defaults (Code)
- Base configuration values defined in code
- Safe, non-sensitive defaults
- Required for application to start
- Example: default timeout values, default limits

### Layer 2: Environment Files
- .env files for environment-specific values
- Never committed to version control
- Loaded at application startup
- Override defaults

### Layer 3: Secrets Store (Future)
- For production: external secrets manager
- Vault, AWS Secrets Manager, or similar
- Encrypted at rest
- Rotated regularly

## Environment Variable Naming

### Naming Convention
- Prefix: QUANTX_ for application-specific
- UPPER_CASE with underscores
- Descriptive names, no abbreviations

### Core Variables

# Application
QUANTX_ENV=local|development|staging|production
QUANTX_DEBUG=false
QUANTX_LOG_LEVEL=INFO
QUANTX_SECRET_KEY=<random-64-char-string>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/quantx
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Cache
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# AI Providers
GEMINI_API_KEY=<api-key>
OPENROUTER_API_KEY=<api-key>
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDER=openrouter

# Exchanges
EXCHANGE_BINANCE_API_KEY=<key>
EXCHANGE_BINANCE_SECRET=<secret>

# Telegram
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_ALLOWED_USERS=<user-id>

# CORS
CORS_ORIGINS=http://localhost:3000,https://trading.example.com
CORS_ALLOW_CREDENTIALS=true

### Naming Patterns
- Boolean: FEATURE_X_ENABLED or FEATURE_X
- Timeouts: {SERVICE}_TIMEOUT_{UNIT}
- URLs: {SERVICE}_URL
- Paths: {SERVICE}_PATH

## Configuration File Formats

### YAML (Application Config)
- app: name, version, debug settings
- database: pool_size, max_overflow, echo
- redis: max_connections, socket_timeout
- trading: default_exchange, paper_trading, max_open_orders
- risk: max_position_size, max_daily_loss, stop_loss_percent

### .env (Secrets)
- DATABASE_URL, REDIS_URL
- GEMINI_API_KEY, OPENROUTER_API_KEY
- EXCHANGE_* API keys
- TELEGRAM_BOT_TOKEN

### JSON (Specific Cases)
- migrations: directory, auto_generate
- seed_data: symbols, timeframes

## Settings Validation

### Pydantic Settings
- All settings validated at startup
- Application fails fast on invalid config
- Environment variables documented in .env.example
- Types enforced (no stringly-typed configs)

### Validation Rules
- Required fields validated at startup
- Type coercion and validation
- Environment variable documentation

## Feature Flags

### Definition
- AI_STRATEGIES: Enable LLM strategies
- BACKTESTING: Enable backtesting framework
- PAPER_TRADING_MODE: Sandbox mode flag
- NOTIFICATIONS_ENABLED: Toggle notifications

### Usage
- Check before expensive operations
- Can be toggled without restart (future: admin API)
- Log when feature flag state changes
- Document purpose of each flag

### Tiers
- Alpha: Experimental, may break
- Beta: Stable but not default
- GA: Generally available, always on
- Deprecated: Will be removed

## Configuration Reload

### Current (v1)
- Restart required for config changes
- Environment variables read at startup
- YAML configs loaded once

### Future (v2)
- Hot reload of non-sensitive configs
- Signal-based reload (SIGHUP)
- Feature flags toggleable via API
- Secrets rotation without restart
