# Configuration Standards

## 1. Configuration Philosophy

Configuration in QuantX AI must be **secure by default**, **environment-aware**, and **validated at startup**. Secrets and credentials are NEVER hardcoded.

## 2. Configuration Sources (Priority Order)

Configuration is loaded in this order (later overrides earlier):

```python
# Priority 1: Defaults
# Priority 2: .env file (not committed)
# Priority 3: Environment variables
# Priority 4: Mounted Docker secrets (production)
```

**Implementation** (Pydantic Settings):

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    # Application
    app_name: str = "QuantX AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: str
    redis_pool_size: int = 10

    # Exchange API credentials (per exchange)
    exchange_credentials: dict[str, ExchangeCredentials] = {}

    # AI providers
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_max_tokens: int = 1000
    openrouter_api_key: str | None = None
    openrouter_fallback_model: str = "openai/gpt-4o-mini"

    # Telegram
    telegram_bot_token: str
    telegram_webhook_url: str | None = None
    telegram_allowed_users: set[int] = set()

    # Logging
    log_format: str = "json"  # or "text" for local dev
    log_file: str | None = None

    # Feature flags
    feature_new_ui: bool = False
    feature_dark_mode: bool = True
    feature_advanced_charting: bool = False

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
```

## 3. Environment Variable Naming

All environment variables use `QUANTX_` prefix in UPPER_SNAKE_CASE.

```bash
# Application
QUANTX_APP_NAME=QuantX AI
QUANTX_APP_VERSION=0.1.0
QUANTX_ENVIRONMENT=production
QUANTX_LOG_LEVEL=INFO
QUANTX_DEBUG=false

# Server
QUANTX_HOST=0.0.0.0
QUANTX_PORT=8000
QUANTX_WORKERS=4

# Database
QUANTX_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/quantx
QUANTX_DATABASE_POOL_SIZE=5
QUANTX_DATABASE_MAX_OVERFLOW=10
QUANTX_DATABASE_ECHO=false

# Redis
QUANTX_REDIS_URL=redis://localhost:6379/0
QUANTX_REDIS_POOL_SIZE=10

# Exchange (per exchange)
QUANTX_EXCHANGE_BINANCE_API_KEY=your_api_key
QUANTX_EXCHANGE_BINANCE_SECRET=your_secret
QUANTX_EXCHANGE_BINANCE_SANDBOX=true

# AI
QUANTX_GEMINI_API_KEY=your_gemini_key
QUANTX_OPENROUTER_API_KEY=your_openrouter_key

# Telegram
QUANTX_TELEGRAM_BOT_TOKEN=your_telegram_token
QUANTX_TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook
QUANTX_TELEGRAM_ALLOWED_USERS=12345678,87654321

# Security
QUANTX_SECRET_KEY=your_secret_key_for_jwt_signing
QUANTX_JWT_ALGORITHM=HS256
QUANTX_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Feature flags
QUANTX_FEATURE_NEW_UI=false
```

**Rules**:
- No prefix for single-letter env vars (e.g., `PORT`, not `QUANTX_PORT`)
- Nested configs use double underscore `__`
- Boolean values: `true`/`false` (case-insensitive)

## 4. Configuration by Layer

### 4.1 Domain Layer Configuration
Domain layer configures ONLY business rules. No framework/settings.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TradingRulesConfig:
    """Pure domain configuration for trading rules."""

    min_order_quantity: Decimal  # Minimum trade size
    max_position_value: Decimal  # Maximum single position value
    allowed_order_sides: set[OrderSide]
    trading_hours: frozenset[TimeRange]  # When trading is allowed
    max_open_orders: int  # Per symbol or global
```

**Construction**: Passed down from application layer, never loaded from env.

```python
# application/use_cases/place_order.py
class PlaceOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        trading_rules: TradingRulesConfig,  # Injected configuration
    ):
        self._order_repo = order_repository
        self._trading_rules = trading_rules

    async def execute(self, command: PlaceOrderCommand) -> OrderId:
        if command.quantity < self._trading_rules.min_order_quantity:
            raise ValidationError(f"Quantity below minimum: {self._trading_rules.min_order_quantity}")
        ...
```

### 4.2 Application Layer Configuration
Application orchestrates using injected configuration.

```python
from pydantic_settings import BaseSettings

class ApplicationSettings(BaseSettings):
    """Application-level settings."""

    trading_rules: TradingRulesConfig
    exchange_timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_backoff: float = 2.0
    event_batch_size: int = 100
    market_data_refresh_interval: int = 60  # seconds
```

### 4.3 Infrastructure Configuration
Infrastructure layer receives DSN URLs, connection strings.

```python
class DatabaseSettings(BaseSettings):
    """Database connection configuration."""

    url: str
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

    @property
    def async_url(self) -> str:
        """Ensure asyncpg driver."""
        if not self.url.startswith("postgresql+asyncpg://"):
            return self.url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.url


class RedisSettings(BaseSettings):
    """Redis connection configuration."""

    url: str
    pool_size: int = 10
    decode_responses: bool = True
```

### 4.4 Presentation Layer Configuration
Presentation layer uses feature flags and UI settings.

```python
class PresentationSettings(BaseSettings):
    """Presentation layer settings."""

    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    # Feature flags
    enable_ai_analysis: bool = True
    enable_websocket: bool = True
    enable_telegram: bool = True
    enable_reporting: bool = True
```

## 5. Configuration Files

### 5.1 .env.example
Template for local development (committed, no secrets):

```bash
# QuantX AI Environment Configuration Template
# Copy to .env and fill in values

# Application
QUANTX_ENVIRONMENT=development
QUANTX_LOG_LEVEL=DEBUG

# Database (local development)
QUANTX_DATABASE_URL=postgresql+asyncpg://quantx:quantx@localhost:5432/quantx

# Redis (local development)
QUANTX_REDIS_URL=redis://localhost:6379/0

# Exchange API (testnet)
QUANTX_EXCHANGE_BINANCE_API_KEY=your_testnet_key
QUANTX_EXCHANGE_BINANCE_SECRET=your_testnet_secret
QUANTX_EXCHANGE_BINANCE_SANDBOX=true

# AI (get your own keys)
QUANTX_GEMINI_API_KEY=your_gemini_key_here

# Telegram (create bot via @BotFather)
QUANTX_TELEGRAM_BOT_TOKEN=your_telegram_token_here

# Security
QUANTX_SECRET_KEY=generate_random_secret_key
```

### 5.2 .env Adjustment Logic

First `.env` adjustment is automatic via settings classes:

```python
# When one config changes, cascade updates others
if QUANTX_ENVIRONMENT == "production":
    QUANTX_LOG_LEVEL = "WARNING"
    QUANTX_DATABASE_POOL_SIZE = 10
    QUANTX_WORKERS = 4
```

### 5.3 JSON/YAML Configuration (Complex Configs)

```yaml
# config/exchanges/binance.yaml
exchange: binance
api_key: ${QUANTX_EXCHANGE_BINANCE_API_KEY}
secret: ${QUANTX_EXCHANGE_BINANCE_SECRET}
sandbox: true
timeout: 30000
rate_limit: 1200  # per minute
supported_timeframes: [1m, 5m, 15m, 1h, 4h, 1d]

# config/strategies/default.yaml
name: default
max_positions: 5
risk_per_trade: 0.02  # 2% of portfolio
stop_loss_atr_multiplier: 2.0
take_profit_atr_multiplier: 3.0

# config/ai_prompts/market_analysis.txt
You are QuantX AI trading assistant.
Analyze: {symbol} on {timeframe}
Current price: {current_price}
Recent indicators: {indicators}
```

## 6. Secrets Management

### 6.1 Secrets Storage (Production)

**Never store secrets in code or config files.**

```
Docker Secrets (for production):
/run/secrets/
  ├── gemini_api_key
  ├── telegram_bot_token
  └── exchange_credentials
```

**Access via Docker secrets**:
```python
# infrastructure/config/secrets.py
def load_secret(name: str) -> str:
    """Load secret from Docker secrets."""
    secret_path = f"/run/secrets/{name}"
    try:
        with open(secret_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise ConfigurationError(f"Secret {name} not found")

# In Settings class
gemini_api_key: str = Field(default_factory=lambda: load_secret("gemini_api_key"))
```

### 6.2 Secret Permissions

Docker to host mount:
```yaml
services:
  api:
    secrets:
      - gemini_api_key
      - telegram_bot_token

secrets:
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
  telegram_bot_token:
    file: ./secrets/telegram_bot_token.txt
```

**Host file permissions**:
```bash
chmod 600 ./secrets/*
chown root:root ./secrets/*
# Amazon ECS/Docker secrets: restricted access
```

### 6.3 Secret Rotation

Support hot-reloading of secrets without restart:

```python
class SecretManager:
    """Manages secrets with hot-reload capability."""

    def __init__(self, secret_names: list[str]):
        self._secrets = {}
        self._paths = {name: f"/run/secrets/{name}" for name in secret_names}
        self._load_all()

    def _load_all(self) -> None:
        for name, path in self._paths.items():
            try:
                with open(path, "r") as f:
                    self._secrets[name] = f.read().strip()
            except FileNotFoundError:
                continue

    def get(self, name: str) -> str:
        if name not in self._secrets:
            raise SecretNotFoundError(name)
        return self._secrets[name]

    async def watch_for_changes(self) -> None:
        """Watch for secret file changes and reload."""
        import watchfiles
        async for changes in watchfiles.awatch(*self._paths.values()):
            logger.info("Secrets file changed, reloading", extra={"changes": changes})
            self._load_all()
```

## 7. Configuration Validation

### 7.1 Pydantic Validation Rules

```python
class DatabaseSettings(BaseSettings):
    url: str = Field(pattern=r"^postgresql\+asyncpg://.*")
    pool_size: int = Field(ge=1, le=50)
    max_overflow: int = Field(ge=0, le=100)


class AIProviderSettings(BaseSettings):
    gemini_api_key: str = Field(min_length=20)
    gemini_model: str = Field(pattern=r"^gemini-\d+\.\d+-(flash|pro)(?:-thinking)?$")
    gemini_max_tokens: int = Field(ge=1, le=10000)
```

### 7.2 Runtime Validation

Settings are validated on application startup. Invalid configuration prevents startup.

```python
def validate_configuration(settings: Settings) -> None:
    """Post-load validation."""
    if settings.environment == "production":
        if settings.debug:
            raise ConfigurationError("Debug mode must be disabled in production")
        if not settings.database_url.startswith("postgresql+asyncpg://"):
            raise ConfigurationError("Production requires asyncpg driver")
        if not settings.secret_key or len(settings.secret_key) < 32:
            raise ConfigurationError("SECRET_KEY must be at least 32 characters")
```

## 8. Multiple Environments

### 8.1 Environment Detection

```python
import os

ENVIRONMENT = os.getenv("QUANTX_ENVIRONMENT", "development").lower()

VALID_ENVIRONMENTS = {"development", "testing", "staging", "production"}

if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ConfigurationError(
        f"Invalid environment: {ENVIRONMENT}. Must be one of {VALID_ENVIRONMENTS}"
    )
```

### 8.2 Environment-Specific Defaults

```python
class EnvironmentConfig:
    """Environment-specific configuration overrides."""

    @staticmethod
    def get_database_url(env: str) -> str:
        match env:
            case "development":
                return "postgresql+asyncpg://quantx:quantx@localhost:5432/quantx"
            case "testing":
                return "postgresql+asyncpg://quantx:quantx@localhost:5432/quantx_test"
            case "staging":
                return os.getenv("QUANTX_DATABASE_URL")
            case "production":
                return os.getenv("QUANTX_DATABASE_URL")
            case _:
                raise ConfigurationError(f"Unknown environment: {env}")
```

### 8.3 Environment Matrix

| Environment | Database | Redis | Exchanges | AI | Log Level | Workers |
|-------------|----------|-------|-----------|-----|-----------|---------|
| development | local | local | sandbox | gemini | DEBUG | 1 |
| testing | local | local | mock | disabled | WARNING | 2 |
| staging | prod-like | prod-like | prod-like | prod | INFO | 2 |
| production | primary | primary | production | production | WARNING | 4 |

## 9. Configuration Hot-Reload

### 9.1 Feature Flags

Feature flags can be toggled without restart.

```python
class FeatureFlags(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.features")

    enable_new_ui: bool = False
    enable_dark_mode: bool = True
    enable_advanced_charting: bool = False
    enable_strategy_backtesting: bool = True
    enable_ai_analysis: bool = True

    async def watch(self) -> None:
        """Watch feature flag file and reload on change."""
        ...
```

### 9.2 Live Configuration Update

```python
class LiveConfiguration:
    """Hot-reloadable configuration."""

    def __init__(self, config: Settings):
        self._config = config
        self._listeners: list[Callable] = []

    def on_change(self, callback: Callable) -> None:
        self._listeners.append(callback)

    async def update(self, key: str, value: Any) -> None:
        old_value = getattr(self._config, key)
        setattr(self._config, key, value)
        for callback in self._listeners:
            await callback(key, old_value, value)
```

## 10. Configuration Documentation

### 10.1 Self-Documenting Configuration

Generate config docs automatically:

```python
# config/docs.py
def generate_configuration_docs(settings: BaseSettings) -> str:
    """Generate markdown documentation from Pydantic Settings."""
    lines = ["# Configuration Options\n"]
    for name, field in settings.model_fields.items():
        lines.append(f"## {name}\n")
        lines.append(f"Type: `{field.annotation}`\n")
        lines.append(f"Default: {field.default}")
        if field.description:
            lines.append(f"\n{field.description}\n")
    return "\n".join(lines)
```

### 10.2 Configuration Validation Output

```python
def print_configuration_summary(settings: Settings) -> None:
    """Print configuration summary on startup (redacted)."""
    config_data = settings.model_dump()
    # Hide secrets
    secure_data = {
        k: ("***" if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower() else v)
        for k, v in config_data.items()
    }
    logger.info("Configuration loaded", extra={"config": secure_data})
```

## 11. Configuration Anti-Patterns

### 11.1 NEVER Do These

```python
# NEVER: Hardcode configuration
DATABASE_URL = "postgresql://localhost/quantx"  # BANNED

# NEVER: Use global mutable configuration
CONFIG = {"database_url": "..."}  # BANNED - global mutable state

# NEVER: Load from unvalidated source
config = json.load(open("config.json"))  # BANNED - no validation
```

### 11.2 ALWAYS Do These

```python
# ALWAYS: Use typed settings with validation
class Settings(BaseSettings):
    database_url: str = Field(pattern=r"^postgresql\+asyncpg://.*")

# ALWAYS: Use dependency injection
settings = Settings()  # Single instance, injected everywhere

# ALWAYS: Fail fast on invalid config
try:
    settings = Settings()
    validate_configuration(settings)
except ValidationError as e:
    logger.critical("Invalid configuration", exc_info=True)
    sys.exit(1)
```

## 12. Configuration in Tests

### 12.1 Test Configuration Override

```python
import pytest

@pytest.fixture
def test_settings() -> Generator[Settings, None, None]:
    """Override settings for testing."""
    original = os.environ.copy()
    os.environ["QUANTX_DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/quantx_test"
    os.environ["QUANTX_LOG_LEVEL"] = "WARNING"
    settings = Settings()
    yield settings
    # Restore
    os.environ.clear()
    os.environ.update(original)
```

### 12.2 Mock Settings

```python
class MockSettings(BaseSettings):
    """Mock settings for unit testing."""
    database_url: str = "postgresql+asyncpg://mock:mock@localhost/mock"
    redis_url: str = "redis://localhost:6379/0"
    gemini_api_key: str = "mock_key"
    exchange_credentials: dict = {}
```
