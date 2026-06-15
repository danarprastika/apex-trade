# APEX Financial Intelligence Platform

Version: 0.1
Status: Draft
Document Type: Domain Model

---

# 1. Purpose

Dokumen ini mendefinisikan seluruh entitas inti (Domain Entities) yang menjadi fondasi:

- Database Design
- API Design
- AI Architecture
- Trading Architecture
- Telegram Architecture
- Web Architecture

Semua modul wajib menggunakan domain model ini sebagai sumber kebenaran.

---

# 2. Domain Overview

Core Domains:

1. Identity Domain
2. Exchange Domain
3. Market Domain
4. Trading Domain
5. Portfolio Domain
6. Intelligence Domain
7. AI Domain
8. Research Domain
9. Monitoring Domain
10. System Domain

---

##################################################
# IDENTITY DOMAIN
##################################################

# 3. User

Description:

Representasi pengguna sistem.

Attributes:

- id
- username
- email
- password_hash
- role
- status
- created_at
- updated_at

Relationships:

User
 ├─ ExchangeAccount
 ├─ Portfolio
 ├─ Trade
 ├─ Notification
 └─ Settings

---

# 4. Role

Description:

Hak akses pengguna.

Types:

- SUPER_ADMIN
- ADMIN
- TRADER
- VIEWER

---

# 5. UserSettings

Description:

Konfigurasi personal user.

Attributes:

- timezone
- language
- theme
- notification_settings

---

##################################################
# EXCHANGE DOMAIN
##################################################

# 6. Exchange

Description:

Representasi broker/exchange.

Examples:

- Binance
- Bybit
- OKX

Attributes:

- id
- name
- type
- status

---

# 7. ExchangeAccount

Description:

Koneksi akun user ke exchange.

Attributes:

- id
- user_id
- exchange_id
- api_key
- api_secret_encrypted
- status

Relationships:

ExchangeAccount
 ├─ Orders
 ├─ Positions
 └─ Balances

---

##################################################
# MARKET DOMAIN
##################################################

# 8. Asset

Description:

Aset yang dapat diperdagangkan.

Examples:

BTC
ETH
SOL
XAUUSD

Attributes:

- symbol
- name
- asset_type

Asset Types:

- CRYPTO
- FOREX
- STOCK
- ETF
- COMMODITY
- INDEX

---

# 9. MarketPair

Examples:

BTCUSDT
ETHUSDT

Attributes:

- base_asset
- quote_asset
- exchange

---

# 10. Candle

Description:

Data OHLCV.

Attributes:

- pair
- timeframe
- open
- high
- low
- close
- volume
- timestamp

---

# 11. OrderBookSnapshot

Attributes:

- bids
- asks
- spread
- timestamp

---

# 12. FundingRate

Attributes:

- pair
- rate
- timestamp

---

# 13. OpenInterest

Attributes:

- pair
- value
- timestamp

---

##################################################
# INTELLIGENCE DOMAIN
##################################################

# 14. NewsArticle

Attributes:

- title
- source
- category
- sentiment
- impact_score
- published_at

---

# 15. NewsSource

Examples:

Reuters
Bloomberg
CoinDesk

Attributes:

- source_name
- reliability_score

---

# 16. SentimentRecord

Attributes:

- platform
- asset
- sentiment_score
- confidence_score
- timestamp

Platforms:

- Twitter/X
- Reddit
- Telegram
- Discord

---

# 17. MacroEvent

Examples:

FOMC
CPI
GDP
NFP

Attributes:

- event_name
- country
- impact_level
- release_date

---

# 18. WhaleActivity

Attributes:

- asset
- amount
- direction
- source
- timestamp

Directions:

- IN
- OUT

---

##################################################
# TRADING DOMAIN
##################################################

# 19. Strategy

Description:

Trading strategy.

Attributes:

- id
- name
- version
- status
- description

Status:

- ACTIVE
- INACTIVE
- TESTING
- RETIRED

---

# 20. Signal

Description:

Output dari strategi.

Attributes:

- pair
- action
- confidence
- reason
- timestamp

Actions:

- BUY
- SELL
- HOLD

---

# 21. Order

Description:

Order yang dikirim ke exchange.

Attributes:

- order_id
- pair
- type
- side
- quantity
- price
- status

---

# 22. Position

Description:

Posisi aktif.

Attributes:

- pair
- entry_price
- quantity
- pnl
- status

Status:

- OPEN
- CLOSED

---

# 23. Trade

Description:

Riwayat trade.

Attributes:

- strategy
- entry
- exit
- pnl
- duration

---

##################################################
# PORTFOLIO DOMAIN
##################################################

# 24. Portfolio

Attributes:

- owner
- total_value
- total_profit
- risk_score

---

# 25. PortfolioAllocation

Attributes:

- asset
- percentage
- target_percentage

---

# 26. PortfolioSnapshot

Attributes:

- timestamp
- total_value
- cash
- exposure

---

##################################################
# RISK DOMAIN
##################################################

# 27. RiskProfile

Attributes:

- max_drawdown
- max_daily_loss
- risk_per_trade

---

# 28. RiskEvent

Attributes:

- event_type
- severity
- description
- timestamp

---

# 29. ExposureRecord

Attributes:

- asset
- exposure
- timestamp

---

##################################################
# AI DOMAIN
##################################################

# 30. AIModel

Attributes:

- model_name
- version
- accuracy
- status

Status:

- TRAINING
- ACTIVE
- RETIRED

---

# 31. Prediction

Attributes:

- asset
- prediction_type
- value
- confidence

---

# 32. AIAgent

Examples:

Market Agent
News Agent
Risk Agent

Attributes:

- agent_name
- version
- status

---

# 33. AgentDecision

Attributes:

- agent
- recommendation
- confidence

---

# 34. FinalDecision

Attributes:

- decision
- confidence
- reasoning

---

##################################################
# MEMORY DOMAIN
##################################################

# 35. MemoryRecord

Description:

Long-term AI memory.

Attributes:

- memory_type
- content
- source
- timestamp

---

# 36. KnowledgeNode

Description:

Knowledge Graph Node.

Attributes:

- node_type
- node_name

---

# 37. KnowledgeRelation

Description:

Knowledge Graph Edge.

Attributes:

- source_node
- target_node
- relation_type

---

##################################################
# RESEARCH DOMAIN
##################################################

# 38. Experiment

Description:

AI Research Experiment.

Attributes:

- hypothesis
- result
- status

Status:

- RUNNING
- SUCCESS
- FAILED

---

# 39. BacktestRun

Attributes:

- strategy
- start_date
- end_date
- profit_factor
- drawdown

---

# 40. PaperTrade

Attributes:

- signal
- entry
- exit
- pnl

---

##################################################
# MONITORING DOMAIN
##################################################

# 41. SystemMetric

Attributes:

- metric_name
- metric_value
- timestamp

---

# 42. SystemAlert

Attributes:

- alert_type
- severity
- message

---

##################################################
# NOTIFICATION DOMAIN
##################################################

# 43. Notification

Attributes:

- user
- title
- content
- status

Status:

- PENDING
- SENT
- FAILED

---

##################################################
# AUDIT DOMAIN
##################################################

# 44. AuditLog

Attributes:

- actor
- action
- entity
- timestamp

---

# 45. Domain Rules

Rule 1

Trade wajib berasal dari Signal.

Signal → Trade

---

Rule 2

Trade wajib terkait Strategy.

Strategy → Signal → Trade

---

Rule 3

Risk Engine dapat membatalkan keputusan AI.

AI Decision
↓
Risk Validation
↓
Execution

---

Rule 4

Model baru tidak boleh digunakan tanpa validasi.

Training
↓
Backtest
↓
Validation
↓
Deployment

---

Rule 5

Semua keputusan AI wajib memiliki alasan.

No Black Box Decisions.

---

# End of Domain Model