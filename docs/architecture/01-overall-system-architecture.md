# Overall System Architecture

## 1. System Context

QuantX AI is a single-user, personal AI trading platform deployed on a Linux VPS.

### 1.1 External Systems

| System | Purpose | Integration Pattern |
|--------|---------|---------------------|
| Cryptocurrency Exchanges (CCXT) | Market data, order execution | REST API / WebSocket |
| Telegram | User notifications, command interface | Bot API (aiogram) |
| Gemini API | Primary LLM for AI strategy | REST API |
| OpenRouter | Fallback LLM provider | REST API |
| PostgreSQL | Persistent storage | Local driver |
| Redis | Caching, session state, pub/sub | Local driver |

### 1.2 User Personas

- **Trader (Single User)**: The sole operator who configures strategies, monitors portfolio, and executes trades.

## 2. High-Level Architecture

The system follows Clean Architecture with four layers: Domain, Application, Infrastructure, and Presentation.

## 3. Core Components

### 3.1 API Gateway / Router
- FastAPI application entry point
- Request routing, middleware pipeline, WebSocket management
- Authentication enforcement
- Rate limiting

### 3.2 Domain Services
- **Trading Service**: Order lifecycle, execution logic
- **Market Data Service**: Data ingestion, normalization, caching
- **Portfolio Service**: Position tracking, P&L calculation
- **Risk Service**: Risk metrics, limits, alerts
- **AI Service**: Strategy generation, signal processing
- **Strategy Service**: Strategy orchestration, backtesting coordination
- **Notification Service**: Telegram messaging, in-app alerts
- **User Service**: Single-user profile, preferences, API key management

### 3.3 Infrastructure Adapters
- **Exchange Adapters**: CCXT wrappers per exchange
- **Repository Implementations**: SQLAlchemy-based data access
- **AI Clients**: Gemini/OpenRouter API clients
- **Telegram Client**: aiogram bot implementation
- **Cache Client**: Redis operations

## 4. Data Flow Patterns

### 4.1 Market Data Flow
Exchange API -> CCXT Adapter -> Market Data Service -> Redis Cache -> Domain Entity -> Repository -> PostgreSQL -> WebSocket -> Frontend

### 4.2 Trading Execution Flow
AI Strategy -> Signal -> Risk Service (validate) -> Trading Service -> Exchange Adapter -> Order -> Repository -> Notification

### 4.3 User Command Flow
Telegram / Web UI -> API Router -> Service -> Domain -> Repository -> Response -> Telegram / WebSocket -> User

## 5. Infrastructure Topology

Internet -> Nginx (SSL, Rate Limiting) -> FastAPI (Uvicorn) -> Redis/PostgreSQL

## 6. Non-Functional Architecture

### 6.1 Availability
- Target: 99.5% uptime for trading operations
- Graceful degradation: cached data when exchange APIs fail
- Health check endpoints for all services

### 6.2 Performance
- API response time: < 200ms (p95)
- Market data latency: < 500ms end-to-end
- Frontend initial load: < 2s

### 6.3 Scalability
- Horizontal scaling via stateless FastAPI workers
- Database read replicas for reporting queries
- Redis clustering for high-throughput caching

### 6.4 Resilience
- Circuit breakers for external API calls
- Retry with exponential backoff
- Dead letter queues for failed notifications
- Database connection pooling
