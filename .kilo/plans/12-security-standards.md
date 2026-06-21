# Security Standards

QuantX AI is an **autonomous trading system** trading with real money. Security is paramount and must follow industry-standard, battle-tested practices. This document defines the security architecture, policies, and implementation requirements.

## 1. Security Architecture

### 1.1 Protection Goals

| Asset | Protection Required | Implementation |
|-------|---------------------|-output|
| Exchange API Keys | Encryption at rest and in transit | Vault, mTLS |
| AI API Keys | Encryption at rest | Vault with transit |
| User Authentication | Telegram + JWT | MFA, session management |
| Trade Execution | Authorization checks | RBAC, signing |
| Audit Trails | Immutable audit logs | WORM storage, cryptographic signing |
| Configuration | Integrity verification | Signed configs, validation |

### 1.2 Threat Model

**Trusted Zone**:
- Backend application processes (FastAPI, workers)
- PostgreSQL database (with access controls)
- Redis cache (isolated network)

**Semi-Trusted Zone**:
- Docker network (container-to-container)
- CCXT exchange libraries (third-party code)

**Untrusted Zone**:
- Internet (Telegram, exchanges, AI APIs)
- User-supplied input (any external source)

### 1.3 Defense-in-Depth

```
Layer 7: Authentication (Telegram user verification, JWT)
Layer 6: Authorization (Order-level checks)
Layer 5: Input Validation (Pydantic schemas, strict typing)
Layer 4: Transport Security (TLS 1.3, WSS)
Layer 3: Network Isolation (Docker network, firewall)
Layer 2: Data Security (AES-256 encryption, audit logging)
Layer 1: Infrastructure Security (SSH keys, UFW, automatic updates)
```

## 2. Authentication and Authorization

### 2.1 Primary Authentication: Telegram OAuth

```python
class TelegramAuthenticator:
    """Authenticate users via Telegram."""

    async def authenticate(self, telegram_user_id: int) -> User:
        user = await self._user_repo.find_by_telegram_id(telegram_user_id)
        if not user:
            user = await self._user_repo.create(telegram_id=telegram_user_id)
        return user
```

**Process**:
1. Verify Telegram webhook payload signature
2. Extract `telegram_user_id` from validated payload
3. Look up or create user in local database
4. Issue session token (for API access)

### 2.2 Session Management

```python
class SessionManager:
    """Manage user sessions."""

    SESSION_TTL = 24 * 60 * 60  # 24 hours

    async def create_session(self, user_id: UUID) -> str:
        session_token = self._generate_secure_token()
        await self._redis.setex(
            f"session:{session_token}",
            self.SESSION_TTL,
            str(user_id),
        )
        return session_token

    async def validate_session(self, token: str) -> User | None:
        user_id = await self._redis.get(f"session:{token}")
        if user_id:
            await self._redis.expire(f"session:{token}", self.SESSION_TTL)
            return await self._user_repo.find_by_id(user_id)
        return None
```

### 2.3 JWT for API

```python
import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: UUID) -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
```

## 3. Cryptographic Practices

### 3.1 Encryption Policy

| Usage | Algorithm | Key Length | Notes |
|-------|-----------|-----------|-------|
| API keys at rest | AES-256-GCM | 256 bits | Per-field encryption |
| Passwords | Argon2id | auto | Not applicable (Telegram OAuth only) |
| Data transmission | TLS 1.3 | - | Enforced everywhere |
| JWT signing | HS256 or RS256 | 256+ bits | Rotate quarterly |

### 3.2 Key Management

```python
class KeyManager:
    """Manage cryptographic keys."""

    def __init__(self):
        self._master_key = self._load_or_generate_key("master_key")

    def _load_or_generate_key(self, key_name: str) -> bytes:
        key_path = f"/run/secrets/{key_name}"
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        return os.urandom(32)  # 256-bit key
```

### 3.3 Secret Rotation

```python
# Rotation schedule
ROTATION_SCHEDULE = {
    "jwt_signing_key": timedelta(days=90),
    "api_encryption_key": timedelta(days=90),
    "session_secret": timedelta(days=30),
}
```

## 4. Transport Security

### 4.1 TLS Configuration

```nginx
# Nginx SSL configuration (production)
server {
    listen 443 ssl http2;
    server_name quantx.example.com;

    ssl_certificate /etc/letsencrypt/live/quantx.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/quantx.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

### 4.2 Certificate Management (mkcert)

For ProtonVPN private network or internal domains:
```bash
mkcert quantx.localhost 127.0.0.1 ::1
# Generated certs trusted by browser/OS
```

### 4.3 WebSocket Security

```python
# Secure WebSocket with origin validation
class SecureWebSocketManager:
    async def validate_connection(self, websocket: WebSocket) -> bool:
        origin = websocket.headers.get("origin")
        allowed_origins = settings.cors_origins
        if origin not in allowed_origins:
            logger.warning(
                "WebSocket connection rejected",
                extra={"origin": origin}
            )
            await websocket.close(code=1008, reason="Origin not allowed")
            return False
        return True
```

## 5. Input Validation

### 5.1 Pydantic Whistle-Blowing

```python
class PlaceOrderRequest(BaseModel):
    """Strict validation on all inputs."""

    model_config = ConfigDict(
        strict=True,  # Reject extra fields
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    symbol: Annotated[str, Field(pattern=r"^[A-Z]{3,10}/[A-Z]{3,10}$")]
    side: Literal["buy", "sell"]
    type: Literal["market", "limit", "stop-loss", "take-profit"]
    quantity: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=8)]
    price: Annotated[Decimal, Field(gt=0)] | None = None
    stop_price: Annotated[Decimal, Field(gt=0)] | None = None
```

### 5.2 SQL Injection Prevention

SQLAlchemy ORM with parameterized queries (automatic, never raw SQL).

```python
# GOOD: ORM parameterized
await session.execute(select(Order).where(Order.symbol == symbol))

# BAD: String formatting
await session.execute(f"SELECT * FROM orders WHERE symbol = '{symbol}'")

# ACCEPTABLE: Raw SQL with parameters
await session.execute(text("SELECT * FROM orders WHERE symbol = :symbol"), {"symbol": symbol})
```

## 6. Data Encryption

### 6.1 Sensitive Field Encryption

```python
from cryptography.fernet import Fernet

class FieldEncryption:
    """Encrypt/decrypt sensitive database fields."""

    def __init__(self, key: bytes):
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()
```

**Fields to encrypt (at minimum)**:
- Exchange API keys
- Exchange API secrets
- Gemini/OpenRouter API keys
- Telegram bot token
- Any PII (names, emails if collected)

### 6.2 Encryption at Rest

PostgreSQL TDE (Transparent Data Encryption) or filesystem-level encryption:

```bash
# LUKS full disk encryption on VPS
cryptsetup open /dev/sda1 quantx_data
mount /dev/mapper/quantx_data /mnt/quantx
```

## 7. Secrets Management

### 7.1 Vault Integration (Production Scale)

For production deployment on Linux VPS:

```python
class VaultClient:
    """Hashicorp Vault client for secrets management."""

    def __init__(self, vault_url: str, vault_token: str):
        self._client = hvac.Client(url=vault_url, token=vault_token)

    async def get_secret(self, path: str) -> dict:
        response = await asyncio.to_thread(
            self._client.secrets.kv.v2.read_secret_version,
            path=path,
        )
        return response["data"]["data"]

    async def get_api_key(self, exchange: str) -> str:
        secret = await self.get_secret(f"exchanges/{exchange}")
        return secret["api_key"]
```

**Secrets Hierarchy**:
```
secret/quantx/
├── exchanges/
│   ├── binance/
│   │   ├── api_key
│   │   └── api_secret
│   └── coinbase/
│       ├── api_key
│       └── api_secret
├── ai/
│   ├── gemini/api_key
│   └── openrouter/api_key
├── telegram/
│   └── bot_token
└── database/
    └── credentials
```

### 7.2 Local Development (.env)

For `.env` file in development, enforce:
```bash
# .gitignore includes:
.env
.env.local
.env.*.local
secrets/
*.key
*.pem
```

### 7.3 Secret Permissions (Docker)

```yaml
services:
  api:
    secrets:
      - gemini_api_key
      - telegram_bot_token
      - exchange_credentials

secrets:
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
  telegram_bot_token:
    file: ./secrets/telegram_bot_token.txt
  exchange_credentials:
    file: ./secrets/exchange_credentials.json
```

**Host file restrictions**:
```bash
chmod 600 ./secrets/*
chown root:root ./secrets
```

## 8. Access Control

### 8.1 Telegram Identity

Primary user verification done via Telegram ID:

```python
TELEGRAM_ALLOWED_USERS = {123456789, 987654321}  # Set from env

class TelegramAuthorizationMiddleware:
    async def __call__(self, handler, event, data):
        user = event.from_user
        if not user or user.id not in TELEGRAM_ALLOWED_USERS:
            logger.warning(
                "Unauthorized Telegram attempt",
                extra={"telegram_id": user.id if user else None}
            )
            await event.answer("Unauthorized access")
            return
        data["user"] = user
        return await handler(event, data)
```

### 8.2 API Key Management

For programmatic access:

```python
class APIKey:
    """API key for programmatic access."""

    def __init__(self, key_hash: str, user_id: UUID, scopes: list[str]):
        self.key_hash = key_hash  # Hashed version (never store plaintext)
        self.user_id = user_id
        self.scopes = scopes  # e.g., ["read:orders", "write:trades"]
        self.created_at = datetime.now(timezone.utc)

    @classmethod
    def create(cls, plaintext_key: str, user_id: UUID, scopes: list[str]) -> Self:
        import hashlib
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        return cls(key_hash=key_hash, user_id=user_id, scopes=scopes)
```

## 9. Authorization

### 9.1 RBAC (Role-Based Access Control)

Future: Permissions per role:
```python
class Role(str, Enum):
    TRADER = "trader"      # Full trading
    VIEWER = "viewer"      # Read-only
    ADMIN = "admin"        # Full system access

PERMISSIONS = {
    Role.TRADER: ["read:portfolio", "write:orders", "read:market_data"],
    Role.VIEWER: ["read:portfolio", "read:market_data"],
    Role.ADMIN: ["*"],
}
```

### 9.2 Order Authorization

```python
class OrderAuthorizationService:
    """Ensure user can place orders."""

    async def can_place_order(self, user: User, order: Order) -> bool:
        # 1. User is authenticated
        if not user:
            raise UnauthorizedError()

        # 2. Symbol is in user's watchlist
        if not await self._watchlist_service.has_symbol(user.id, order.symbol):
            raise ForbiddenError(f"Symbol {order.symbol} not in your watchlist")

        # 3. Risk limits not exceeded
        risk_ok = await self._risk_service.check_order_limits(user, order)
        if not risk_ok:
            raise RiskLimitExceededError()

        return True
```

## 10. Input Validation and Sanitization

### 10.1 External Input Validation

```python
class SymbolValidator:
    """Validate and sanitize trading symbols."""

    ALLOWED_FORMATS = {
        "binance": r"^[A-Z]{3,10}USDT$",
        "coinbase": r"^[A-Z]{2,10}-USD$",
    }

    @classmethod
    def validate(cls, symbol: str, exchange: str | None = None) -> Symbol:
        if not symbol or len(symbol) > 20:
            raise ValidationError("Invalid symbol length")
        # Normalize to internal format (BASE/QUOTE)
        normalized = cls._normalize(symbol)
        return Symbol(normalized)
```

### 10.2 CCXT Parameter Sanitization

```python
def sanitize_ccxt_params(params: dict) -> dict:
    """Remove or sanitize CCXT parameters to prevent injection."""
    blocked_params = {"leverage", "marginMode"}  # Risk controls
    for param in blocked_params:
        params.pop(param, None)
    return params
```

## 11. Security Audit and Monitoring

### 11.1 Audit Logging

```python
class AuditLogger:
    """Structure of audit logs."""

    @staticmethod
    def log_action(
        user_id: UUID,
        action: str,  # CREATE, UPDATE, DELETE
        resource: str,  # "Order", "Portfolio"
        resource_id: UUID,
        changes: dict | None = None,
    ) -> None:
        logger.info(
            "AUDIT",
            extra={
                "audit": True,
                "user_id": str(user_id),
                "action": action,
                "resource": resource,
                "resource_id": str(resource_id),
                "changes": changes,
                "ip_address": "extracted",
                "user_agent": "extracted",
            },
        )
```

### 11.2 Security Events

Track these security events:
- Authentication failures
- Authorization failures
- Rate limiting triggers
- Suspicious patterns (rapid API calls)
- Configuration changes

```python
SECURITY_EVENTS = [
    "auth_failure",
    "auth_success",
    "authz_failure",  # authorization
    "rate_limit_triggered",
    "suspicious_pattern",
    "config_change",
    "data_export",
]
```

### 11.3 Failed Authentication Alerting

```python
if failed_auth_attempts > 5:
    alerting.trigger("AUTH_LOCKOUT", {
        "user_id": user_id,
        "attempts": failed_auth_attempts,
        "time_window_minutes": 10,
    })
```

## 12. Rate Limiting

### 12.1 Rate Limiters

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/orders")
@limiter.limit("10/minute")
async def place_order(request): ...
```

### 12.2 Exchange Rate Limiting

Per-exchange rate limiters to prevent API bans:

```python
PER_EXCHANGE_RATE_LIMITS = {
    "binance": {"requests": 1200, "window": 60},
    "coinbase": {"requests": 10, "window": 1},
    "kraken": {"requests": 15, "window": 1},
}
```

## 13. Web Application Security

### 13.1 CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Never "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### 13.2 Security Headers

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 13.3 CSRF Protection

For web form submissions (future):
```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/settings")
@csrf_protect.validate_csrf
async def update_settings(request):
    ...
```

## 14. Network Security

### 14.1 Firewall Configuration (UFW)

```bash
# /etc/ufw/user.rules
# Allow SSH (22/tcp)
# Allow HTTP/HTTPS (80, 443)
# Deny all other inbound
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw default deny incoming
ufw default allow outgoing
```

### 14.2 Docker Network Isolation

```yaml
# docker-compose.yml
services:
  api:
    networks:
      - backend
    expose:
      - "8000"

  nginx:
    networks:
      - frontend
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

volumes:
  quantx-data:
```

## 15. Dependency Security

### 15.1 Audit Dependencies

```bash
# Regular audit
pip-audit --requirement requirements.txt

# CI enforcement
# - Block builds with critical vulnerabilities
# - Fail on high CVEs in production deps
```

### 15.2 Dependency Pinning

```toml
# pyproject.toml
[tool.poetry.dependencies]
fastapi = "^0.111.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.36"}
pydantic = "^2.9.0"

[tool.poetry.group.dev.dependencies]
pip-audit = "^2.7"
safety = "^3.2"
```

## 16. Security Testing

### 16.1 Penetration Testing Checklist

| Area | Test | Expected |
|------|------|----------|
| Authentication | Test invalid Telegram ID | Unauthorized |
| Authorization | Test order for wrong user | Forbidden |
| Input Validation | SQL injection in order symbol | Sanitized/Rejected |
| Session | Expired session token | 401 Unauthorized |
| Rate Limit | Rapid auth attempts | Locked after 5 |
| API | Missing API key | 401 Unauthorized |

### 16.2 Security Regression Tests

```python
@pytest.mark.asyncio
async def test_sql_injection_prevented() -> None:
    """Verify SQL injection is prevented."""
    malicious_symbol = "'; DROP TABLE orders; --"
    with pytest.raises(ValidationError):
        await use_case.execute(PlaceOrderCommand(symbol=malicious_symbol))

@pytest.mark.asyncio
async def test_unauthorized_user_cannot_place_order() -> None:
    """Verify unauthorized users cannot place orders."""
    unauthorized_user = User(id=UUID("9999-9999-9999"))
    with pytest.raises(UnauthorizedError):
        await use_case.execute(command, user=unauthorized_user)
```

## 17. Secure Coding Practices

### 17.1 Secure Logger Usage

```python
def sanitize_for_logging(data: dict) -> dict:
    """Remove sensitive data from log output."""
    sensitive_keys = {
        "api_key", "secret", "token", "password", "private_key",
        "authorization", "cookie", "set-cookie",
    }
    return {
        k: "***" if k.lower() in sensitive_keys else v
        for k, v in data.items()
    }
```

### 17.2 Avoid Hardcoded Credentials

```python
# NEVER: Hardcoded secrets
API_KEY = "sk_live_abc123"  # BANNED

# ALWAYS: Load from configuration
API_KEY = settings.HARDCODED_API_KEY  # DEPRECATED
API_KEY = settings.GEMINI_API_KEY    # CORRECT
```

## 18. Incident Response Plan

### 18.1 Security Incident Taxonomy

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| P0 | Unauthorized trading, data breach | 1 hour |
| P1 | Compromised key, DDoS active | 4 hours |
| P2 | Exposed logs, rate limit abuse | 24 hours |

### 18.2 Response Procedure

1. **Detect**: Automated alerting triggers investigation
2. **Contain**: Block source, disable keys
3. **Investigate**: Audit logs, identify scope
4. **Remediate**: Rotate keys, patch vulnerabilities
5. **Recover**: Restore service, validate
6. **Post-mortem**: Document, improve controls

## 19. Compliance Considerations

### 19.1 Audit Trails

Retain immutable logs for 7 years. Cryptographically sign monthly blocks.

### 19.2 Data Retention

```python
RETENTION_POLICIES = {
    "trade_records": timedelta(days=2555),  # 7 years
    "order_logs": timedelta(days=2555),
    "performance_logs": timedelta(days=365),
    "debug_logs": timedelta(days=30),
    "error_logs": timedelta(days=90),
}
```

## 20. Security Checklist

- [ ] No secrets in git history
<br>
- [ ] All dependencies audited
<br>
- [ ] TLS 1.3 enforced
<br>
- [ ] CORS configured properly
<br>
- [ ] Rate limiting active
<br>
- [ ] Secrets encrypted at rest
<br>
- [ ] Audit logs enabled
<br>
- [ ] Session timeout configured
<br>
- [ ] Input validation strict
<br>
- [ ] Error messages don't leak internals
