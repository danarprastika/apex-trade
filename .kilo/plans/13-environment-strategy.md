# Deployment Strategy

## 1. Deployment Philosophy

QuantX AI is deployed as a **set of Docker containers** orchestrated by Docker Compose on a single Linux VPS. The architecture prioritizes:
- **Simplicity**: Single VPS, no Kubernetes complexity
- **Reproducibility**: Docker ensures environment consistency
- **Observability**: Health checks, logs, metrics
- **Security**: Minimal attack surface, network isolation
- **Recoverability**: Automated backups, rollback capability

## 2. Infrastructure Components

### 2.1 Infrastructure Diagram (Production)

```
Internet
   ↓ HTTPS/WSS
Nginx (Reverse Proxy + SSL)
   ↓ Internal HTTP
FastAPI (Application Server)
   ↓
PostgreSQL (Database) + Redis (Cache)
   ↓
CCXT (Exchange API Calls)
   ↓
External Exchanges (Binance, Coinbase, etc.)
```

### 2.2 Container Definitions

```
quantx-ai/
├── nginx/                    # Reverse proxy + SSL
│   ├── nginx.conf            # Main config
│   ├── default.conf          # Site config
│   └── ssl/                  # SSL certificates (Let's Encrypt)
├── backend/
│   ├── src/                  # Application code
│   ├── pyproject.toml        # Dependencies
│   ├── Dockerfile            # Multi-stage production build
│   └── Dockerfile.dev        # Development with hot-reload
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile            # Production build
│   └── Dockerfile.dev        # Development build
├── docker-compose.yml        # Production stack
├── docker-compose.dev.yml    # Development stack
└── scripts/
    ├── deploy.sh             # Deployment script
    ├── backup.sh             # Backup script
    └── init_vps.sh           # VPS initialization
```

## 3. VPS Requirements

### 3.1 Minimum Specifications

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| CPU | 2 cores | 4 cores | Handles concurrent requests + market data |
| RAM | 4 GB | 8 GB | PostgreSQL + Redis + FastAPI |
| Disk | 100 GB SSD | 500 GB SSD | Database + logs + cache |
| Network | 1 Gbps | 1 Gbps | Low latency for trading signals |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS | LTS, stable, well-supported |

### 3.2 VPS Providers (Recommendations)

| Provider | Plan | Cost (est) | Why |
|----------|------|------------|-----|
| DigitalOcean | 4GB/2CPU Droplet | $48/mo | Simple, reliable, good support |
| Hetzner | CX32 | €25/mo | Best value for specs |
| Vultr | High Frequency 4GB | $36/mo | NVMe SSD, good network |
| AWS Lightsail | 4GB | $36/mo | Simple managed experience |
| Linode | 4GB | $36/mo | Reliable, good support |

**Recommended**: Hetzner CX32 (best value/performance)

## 4. Docker Compose Configuration

### 4.1 docker-compose.yml Structure

```yaml
# docker-compose.yml
version: "3.9"

services:
  # Nginx Reverse Proxy + SSL Termination
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - certbot/conf:/etc/letsencrypt
      - certbot/www:/var/www/certbot
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - frontend
      - backend

  # FastAPI Application Server
  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    expose:
      - "8000"
    environment:
      QUANTX_ENV: production
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/quantx
      REDIS_URL: redis://redis:6379/0
      TELEGRAM_BOT_TOKEN_FILE: /run/secrets/telegram_bot_token
      GEMINI_API_KEY_FILE: /run/secrets/gemini_api_key
    secrets:
      - telegram_bot_token
      - gemini_api_key
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: "1"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: quantx
      POSTGRES_USER: ${POSTGRES_USER}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    secrets:
      - postgres_password
    restart: unless-stopped
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    secrets:
      - redis_password
    restart: unless-stopped
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
  backend:
    internal: true

volumes:
  postgres_data:
  redis_data:

secrets:
  telegram_bot_token:
    file: ./secrets/telegram_bot_token.txt
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
  postgres_password:
    file: ./secrets/postgres_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
```

## 5. Nginx Configuration

### 5.1 nginx.conf

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] '
                   '"$request" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/rss+xml;

    include /etc/nginx/conf.d/*.conf;
}
```

### 5.2 conf.d/site.conf

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=websocket:10m rate=30r/s;

# Upstream definitions
upstream api {
    server api:8000;
}

upstream frontend {
    server frontend:5173;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name quantx.example.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name quantx.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/quantx.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/quantx.example.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/quantx.example.com/chain.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Frontend (React build)
    location /static/ {
        alias /var/www/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket endpoints
    location /ws/ {
        limit_req zone=websocket burst=50 nodelay;
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;  # Long timeout for WebSocket
    }

    # Telegram webhook
    location /telegram/webhook {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://api;
        proxy_set_header Host $host;
    }

    # Health checks
    location /health {
        access_log off;
        proxy_pass http://api;
    }
}
```

## 6. Dockerfile

### 6.1 Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev/test)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

# Final stage
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r quantx && useradd -r -g quantx quantx

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/

# Set ownership
RUN chown -R quantx:quantx /app

# Run as non-root user
USER quantx

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 6.2 Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## 7. Deployment Process

### 7.1 Deployment Script (deploy.sh)

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."
echo "Environment: ${QUANTX_ENV:-production}"

# Pull latest code
echo "📥 Pulling latest code..."
git fetch origin
git reset --hard origin/${GITHUB_REF_NAME:-main}

# Build and start containers
echo "🔨 Building containers..."
docker compose build --no-cache

echo "🔄 Rolling restart..."
docker compose up -d --force-recreate

# Run database migrations
echo "🗄️ Running migrations..."
docker compose exec api alembic upgrade head

# Verify deployment
echo "✅ Verifying deployment..."
sleep 10
curl -f https://quantx.example.com/health || exit 1

echo "🎉 Deployment complete!"
```

### 7.2 Zero-Downtime Deployment

Docker Compose rolling update:

```yaml
services:
  api:
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        order: start-first
```

### 7.3 Health Check Validation

```python
# Health check endpoints
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/health/ready")
async def readiness() -> dict:
    # Check database connectivity
    db_ok = await database_engine.check()
    redis_ok = await redis_client.ping()

    return {
        "ready": db_ok and redis_ok,
        "database": db_ok,
        "redis": redis_ok,
    }

@app.get("/health/live")
async def liveness() -> dict:
    return {"alive": True}
```

## 8. SSL Certificate Management

### 8.1 Let's Encrypt with Certbot

```bash
# Initial setup
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d quantx.example.com \
  --email admin@example.com \
  --agree-tos \
  --no-eff-email

# Auto-renewal (via cron)
0 12 * * * docker compose run --rm certbot renew --quiet
```

### 8.2 mkcert for Local Domains

```bash
# Install mkcert
brew install mkcert  # macOS
sudo apt install libnss3-tools  # Ubuntu
mkcert -install

# Generate cert
mkcert quantx.localhost 127.0.0.1
# Produces: quantx.localhost+2.pem (cert) and key

# SSH dynamic port forwarding for ProtonVPN
# Configure Nginx .well-known for ACME challenge on VPS
# Then run certbot in Docker container that can reach VPS port
```

## 9. Secrets Management

### 9.1 Email-Based Secret Bootstrap

**Security warning**: If you receive an email, it is sensitive and MUST be handled via:
- Secrets Manager (AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault)
- NEVER log the email content
- Store only hashed identifiers in DB (not PII)

```python
# Handling sensitive email information
class UserContactService:
    """Handle user contact information securely."""

    async def store_contact(self, user_id: UUID, contact_data: ContactData) -> None:
        # Store only hashed identifier; actual email goes to secrets manager
        email_hash = hashlib.sha256(contact_data.email.encode()).hexdigest()
        await self._user_repo.update(user_id, {"email_hash": email_hash})

        # Store actual email in secrets manager
        await self._secrets.store(
            f"contacts/{user_id}/email",
            contact_data.email,
        )
```

### 9.2 Docker Secrets

```yaml
# In docker-compose.yml
secrets:
  telegram_bot_token:
    file: ./secrets/telegram_bot_token.txt
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
  exchange_api_key:
    file: ./secrets/exchange_api_key.txt
  exchange_api_secret:
    file: ./secrets/exchange_api_secret.txt

services:
  api:
    secrets:
      - telegram_bot_token
      - gemini_api_key
      - exchange_api_key
      - exchange_api_secret
```

### 9.3 Secrets Rotation

```python
class SecretRotator:
    """Rotate secrets without downtime."""

    async def rotate_secret(self, name: str) -> None:
        # 1. Generate new secret
        new_secret = await self._secrets_manager.generate(name)

        # 2. Store in secrets manager
        await self._secrets_manager.set(name, new_secret)

        # 3. Rolling restart to pick up new secret
        await self._docker_client.service_update(
            service="api",
            secrets=[f"source={name},target={name}"],
        )

        logger.info(f"Secret {name} rotated successfully")
```

## 10. Backup and Recovery

### 10.1 Backup Configuration

```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups
RETENTION_DAYS=30

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker compose exec postgres pg_dump -U quantx quantx | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Redis backup (if persistence enabled)
echo "Backing up Redis..."
docker compose exec redis redis-cli BGSAVE
docker cp quantx-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Application configuration
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  docker-compose.yml .env secrets/

# Cleanup old backups
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "Backups complete: $BACKUP_DIR"
```

### 10.2 Backup Schedule

```yaml
# Cron jobs on VPS
0 2 * * * /app/scripts/backup.sh  # Daily at 2 AM
0 0 * * 0 /app/scripts/full_backup.sh  # Weekly full backup
```

### 10.3 Restore Procedure

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: restore.sh <backup_file>"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite current database"
read -p "Continue? (yes/no): " confirm
[ "$confirm" != "yes" ] && exit 1

# Stop API
docker compose stop api

# Restore PostgreSQL
gunzip -c $BACKUP_FILE/postgres_*.sql.gz | \
  docker compose exec -T postgres psql -U quantx quantx

# Restart API
docker compose start api

echo "✅ Restore complete"
```

## 11. VPS Provisioning

### 11.1 init_vps.sh

```bash
#!/bin/bash
# scripts/init_vps.sh - Initialize fresh Ubuntu 22.04 VPS

set -e

echo "🔧 Initializing QuantX AI VPS..."

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install -y docker-compose-plugin

# Install Git
apt install -y git

# Configure firewall
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Create application directory
mkdir -p /opt/quantx-ai
chown $USER:$USER /opt/quantx-ai

# Setup backup cron
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/quantx-ai/scripts/backup.sh") | crontab -

echo "✅ VPS initialized. Clone repository to /opt/quantx-ai"
echo "   git clone git@github.com:your-org/quantx-ai.git /opt/quantx-ai"
```

### 11.2 SSH Configuration

```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no

# Copy SSH key to VPS
ssh-copy-id user@quantx.example.com
```

## 12. Monitoring and Alerting

### 12.1 Prometheus + Grafana Setup

```yaml
# docker-compose.monitoring.yml (optional add-on)
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
```

### 12.2 Health Check Monitoring

```bash
#!/bin/bash
# scripts/monitor.sh

# Check if API is responding
if ! curl -sf https://quantx.example.com/health/ready >/dev/null; then
    echo "API health check failed"
    # Send alert via Telegram
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${ADMIN_CHAT_ID}" \
      -d "text=🚨 QuantX AI is down! Please investigate immediately." \
      >/dev/null
    exit 1
fi

# Log metrics
wget -q -O - http://localhost:9090/metrics > /tmp/metrics.txt
```

## 13. Scaling Strategy

### 13.1 Vertical Scaling

Initial deployment: Single VPS with 4vCPU / 8GB RAM

Scaling path:
- 4vCPU / 8GB RAM → 8vCPU / 16GB RAM → 16vCPU / 32GB RAM

No application changes needed - just VPS upgrade.

### 13.2 Horizontal Scaling (Future)

```
Current (Single VPS):
┌────────────────────────────────────────┐
│  VPS: quantx.example.com               │
│  ├── Nginx (proxy)                     │
│  ├── API (2 replicas via compose)      │
│  ├── PostgreSQL (primary)              │
│  └── Redis                              │
└────────────────────────────────────────┘

Scaled (Multi-VPS):
┌────────────────────────────────────────┐
│  Load Balancer (HAProxy/Cloudflare)    │
│  ├── VPS 1: API nodes                  │
│  │   ├── Nginx + API × 3              │
│  │   └── (stateless, scale horizontally)│
│  ├── VPS 2: PostgreSQL                 │
│  │   (single primary for ACID)          │
│  └── VPS 3: Redis Cluster              │
└────────────────────────────────────────┘
```

### 13.3 Stateless Design Principles

API application is **fully stateless**:
- Sessions in Redis
- No local disk writes
- State in PostgreSQL/Redis
- Allows horizontal scaling of API tier

## 14. Rollback Procedures

### 14.1 Git-Based Rollback

```bash
# Rollback to previous version
git log --oneline -10
git revert HEAD
git push origin main

# Automated via CI/CD:
# - Bad health check triggers automatic rollback
# - Manual override available
```

### 14.2 Docker Image Rollback

```bash
# Rollback to previous image
docker compose pull quantx-api:previous
docker compose up -d api

# Verify health check
curl -f https://quantx.example.com/health

# Promote stable image
docker compose up -d api
```

## 15. CI/CD Pipeline

### 15.1 GitHub Actions Workflow

```yaml
name: Deploy Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: quantx
          POSTGRES_PASSWORD: quantx
          POSTGRES_DB: quantx_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd redis-cli ping
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install poetry
      - run: poetry install --with dev
      - run: pytest tests/unit/ tests/integration/
      - run: ruff check src/
      - run: mypy src/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: quantx
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/quantx-ai
            docker compose pull
            docker compose up -d --force-recreate
            docker compose exec api alembic upgrade head
            curl -f https://quantx.example.com/health
```

## 16. Observability in Production

### 16.1 Metrics Collection

```python
from prometheus_client import Counter, Gauge, Histogram

trade_executions = Counter("trades_total", "Total trades executed", ["symbol", "side"])
order_latency = Histogram("order_latency_seconds", "Order execution latency")
api_errors = Counter("api_errors_total", ["endpoint", "method", "status_code"])
```

### 16.2 Logs to File

```yaml
# docker-compose.yml
services:
  api:
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=api,environment=production"
```

### 16.3 Centralized Logging (Loki)

```
future/optional:
- Loki for log aggregation
- Grafana for log visualization
- Alertmanager for alert routing

## 17. Disaster Recovery

### 17.1 RPO/RTO Targets

| Scenario | RPO | RTO | Recovery Steps |
|----------|-----|-----|----------------|
| Database corruption | 1 hour | 30 min | Restore from backup |
| VPS failure | 1 hour | 1 hour | Restore to new VPS |
| Secret leak | 0 | 5 min | Rotate all secrets |
| Data breach | 0 | Immediate | Isolate, audit, rotate |

### 17.2 Backup Schedule

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| PostgreSQL | Daily | 30 days | pg_dump → gzip → S3 |
| Redis | Daily | 30 days | BGSAVE → RDB |
| Configuration | On change | 30 days | Git commit |
| Secrets | On change | 30 days | Encrypted backup |
