# Security Standards

## Authentication Architecture

### Token-Based Authentication
- Single-user system with persistent token
- JWT tokens with 24-hour expiration
- Refresh tokens for session extension (7-day lifetime)
- Tokens stored in secure HTTP-only cookies
- CSRF protection for cookie-based auth

### Password Security
- Argon2id hashing algorithm
- 100,000 iterations minimum
- Salt: per-password random salt
- Password policy: 12+ characters, mixed case, numbers, symbols

### Session Management
- Session identifier: random 32-byte token
- Session store: Redis with TTL
- Session invalidation on logout
- Concurrent sessions: single session only

### API Authentication
- Bearer token in Authorization header
- Token validation on every request
- Token revocation list in Redis
- Rate limiting per token

## API Key Management

### Exchange API Keys
- Encrypted at rest using Fernet (symmetric encryption)
- Stored in database, not environment variables
- Key rotation via Telegram bot command
- Keys scoped to required permissions only

### Rotation Procedure
1. Generate new key pair on exchange
2. Update via secure command (Telegram bot)
3. Verify new key works
4. Revoke old key
5. Audit log of rotation event

### Storage Format
- encrypted_key: gAAAAABk...
- created_at: timestamp
- last_used: timestamp
- exchange: binance
- permissions: [read, trade]

## Secrets Storage

### Development
- .env files (never committed)
- .env.example as template
- Local secrets in OS keychain (future)

### Production
- Docker secrets mounted as files
- Environment variables from VPS config
- No hardcoded secrets in Docker images

### Secrets Management Rules
- Never log secrets
- Never expose secrets in errors
- Rotate secrets quarterly
- Audit all secret access
- Backup encrypted secrets

## Encryption Standards

### In-Transit
- TLS 1.3 for all external communications
- Certificate: Let's Encrypt via Nginx
- HSTS header with 1-year max-age
- TLS cipher suite: modern only

### At-Rest
- Database: PostgreSQL
- Backups: Encrypted with GPG
- Secrets: Fernet encryption in database

### Data Protection
- Personal data minimal (single user)
- Financial data accuracy critical
- No third-party data sharing
- Right to delete (local data removal)

## Input Validation

### Validation Layers
1. Schema Validation: Pydantic models at API boundary
2. Type Validation: Strict type checking
3. Range Validation: Numeric bounds (price > 0, quantity > 0)
4. Format Validation: Symbol format, date formats
5. Business Validation: Domain rules after validation

### Validation Rules
- All inputs validated, no exceptions
- Whitelist validation over blacklist
- Maximum input lengths enforced
- Unicode normalization for strings
- Reject unexpected fields

### Sanitization
- Strip HTML/JS from text inputs
- Normalize unicode
- Truncate to maximum length
- Escape SQL parameters (use parameterized queries)

## Rate Limiting

### Nginx Level
- Global: 100 requests/second per IP
- Burst: 200 requests
- Zone: 10MB shared memory

### Application Level
- Authenticated: 60 requests/minute
- Unauthenticated: 10 requests/minute
- WebSocket: 100 messages/minute

### Exchange Level
- Respect each exchange's rate limits
- Track via headers (X-RateLimit-*)
- Backoff when approaching limits
- Queue requests when rate limited

## Security Headers

### Response Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains
- Content-Security-Policy: default-src self; script-src self
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), microphone=(), camera=()

### Cookie Headers
- Secure; HttpOnly; SameSite=Strict

## CORS Configuration

### Allowed Origins
- Development: http://localhost:3000, http://127.0.0.1:3000
- Production: https://trading.example.com (actual domain)
- No wildcard * in production

### Allowed Methods
- GET, POST, PUT, DELETE, OPTIONS
- WebSocket upgrade allowed

### Credentials
- Access-Control-Allow-Credentials: true
- Cookies included in cross-origin requests
- Credentials not cached

## Audit Logging

### Logged Events
- Authentication: login, logout, token refresh
- Authorization: permission checks, admin actions
- Trading: all order placements and modifications
- Configuration: setting changes
- Key management: API key creation, rotation, revocation

### Log Format
- timestamp: ISO 8601
- event_type: order_placed, login, etc.
- actor: user
- action: place_order, login
- resource: order, user
- result: success/failure
- ip_address: client IP
- user_agent: browser/client info

### Retention
- Security logs: 1 year
- Trading logs: 7 years (regulatory)
- Access logs: 1 year
