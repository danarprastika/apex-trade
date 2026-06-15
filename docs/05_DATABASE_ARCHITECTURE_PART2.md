##################################################
# TRADING DOMAIN
##################################################

TABLE: strategies

Purpose:
Menyimpan strategi trading.

Columns:

id UUID PK

name VARCHAR(100)

code VARCHAR(50) UNIQUE

version VARCHAR(20)

description TEXT

strategy_type VARCHAR(50)

status VARCHAR(20)

created_at TIMESTAMP

updated_at TIMESTAMP

Indexes:

code

status

strategy_type

---

Examples:

TREND_FOLLOWING_V1

EMA_CROSS_V1

BREAKOUT_V1

RSI_REVERSAL_V1

---

TABLE: strategy_parameters

Purpose:
Parameter strategi.

Columns:

id UUID PK

strategy_id UUID FK strategies

parameter_name VARCHAR(100)

parameter_value TEXT

created_at TIMESTAMP

Indexes:

strategy_id

---

Example:

EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14

---

TABLE: signals

Purpose:
Output dari strategy engine.

Columns:

id UUID PK

strategy_id UUID FK strategies

market_pair_id UUID FK market_pairs

signal_type VARCHAR(20)

confidence NUMERIC(5,2)

entry_price NUMERIC

stop_loss NUMERIC

take_profit NUMERIC

reason TEXT

signal_time TIMESTAMP

status VARCHAR(20)

Indexes:

strategy_id

market_pair_id

signal_time

status

---

Signal Types:

BUY
SELL
HOLD

---

Signal Status:

PENDING
EXECUTED
REJECTED
EXPIRED

---

TABLE: orders

Purpose:
Order yang dikirim ke exchange.

Columns:

id UUID PK

exchange_account_id UUID FK exchange_accounts

signal_id UUID FK signals

exchange_order_id VARCHAR(255)

order_type VARCHAR(20)

side VARCHAR(20)

quantity NUMERIC

price NUMERIC

filled_quantity NUMERIC

status VARCHAR(20)

created_at TIMESTAMP

updated_at TIMESTAMP

Indexes:

exchange_account_id

signal_id

exchange_order_id

status

---

Order Types:

MARKET
LIMIT
STOP

---

Order Status:

NEW
PARTIALLY_FILLED
FILLED
CANCELLED
REJECTED

---

TABLE: positions

Purpose:
Posisi aktif.

Columns:

id UUID PK

exchange_account_id UUID FK

market_pair_id UUID FK

strategy_id UUID FK

entry_order_id UUID FK orders

entry_price NUMERIC

quantity NUMERIC

current_price NUMERIC

unrealized_pnl NUMERIC

status VARCHAR(20)

opened_at TIMESTAMP

closed_at TIMESTAMP NULL

Indexes:

market_pair_id

strategy_id

status

opened_at

---

Position Status:

OPEN
CLOSED

---

TABLE: trades

Purpose:
Riwayat trade selesai.

Columns:

id UUID PK

position_id UUID FK positions

strategy_id UUID FK strategies

entry_price NUMERIC

exit_price NUMERIC

quantity NUMERIC

gross_profit NUMERIC

net_profit NUMERIC

profit_percentage NUMERIC

duration_minutes INTEGER

opened_at TIMESTAMP

closed_at TIMESTAMP

Indexes:

strategy_id

opened_at

closed_at

profit_percentage

---

##################################################
# PORTFOLIO DOMAIN
##################################################

TABLE: portfolios

Purpose:
Portfolio utama user.

Columns:

id UUID PK

user_id UUID FK users

portfolio_name VARCHAR(100)

currency VARCHAR(20)

total_value NUMERIC

cash_balance NUMERIC

risk_score NUMERIC

created_at TIMESTAMP

updated_at TIMESTAMP

Indexes:

user_id

---

TABLE: portfolio_allocations

Purpose:
Alokasi aset.

Columns:

id UUID PK

portfolio_id UUID FK portfolios

asset_id UUID FK assets

target_percentage NUMERIC

current_percentage NUMERIC

updated_at TIMESTAMP

Indexes:

portfolio_id

asset_id

---

TABLE: portfolio_snapshots

Purpose:
Historical portfolio.

Columns:

id BIGSERIAL PK

portfolio_id UUID FK portfolios

total_value NUMERIC

cash_balance NUMERIC

open_positions INTEGER

daily_pnl NUMERIC

total_pnl NUMERIC

captured_at TIMESTAMP

Indexes:

portfolio_id

captured_at

---

Retention:

Never Delete

---

##################################################
# RISK DOMAIN
##################################################

TABLE: risk_profiles

Purpose:
Aturan risiko user.

Columns:

id UUID PK

user_id UUID FK users

max_risk_per_trade NUMERIC

max_daily_loss NUMERIC

max_drawdown NUMERIC

max_open_positions INTEGER

created_at TIMESTAMP

updated_at TIMESTAMP

Indexes:

user_id

---

Example:

Risk Per Trade = 1%

Max Daily Loss = 3%

Max Drawdown = 15%

---

TABLE: risk_events

Purpose:
Catatan pelanggaran risiko.

Columns:

id UUID PK

user_id UUID FK users

event_type VARCHAR(50)

severity VARCHAR(20)

description TEXT

created_at TIMESTAMP

Indexes:

user_id

event_type

severity

created_at

---

Examples:

MAX_DAILY_LOSS_HIT

MAX_DRAWDOWN_HIT

POSITION_LIMIT_EXCEEDED

---

TABLE: exposure_records

Purpose:
Monitoring eksposur.

Columns:

id BIGSERIAL PK

portfolio_id UUID FK portfolios

asset_id UUID FK assets

exposure_percentage NUMERIC

captured_at TIMESTAMP

Indexes:

portfolio_id

asset_id

captured_at

---

##################################################
# NOTIFICATION DOMAIN
##################################################

TABLE: notifications

Purpose:
Semua notifikasi sistem.

Columns:

id UUID PK

user_id UUID FK users

notification_type VARCHAR(50)

title VARCHAR(255)

message TEXT

status VARCHAR(20)

sent_at TIMESTAMP

created_at TIMESTAMP

Indexes:

user_id

notification_type

status

---

Notification Types:

TRADE_OPENED

TRADE_CLOSED

SIGNAL_GENERATED

RISK_ALERT

SYSTEM_ALERT

NEWS_ALERT

---

Notification Status:

PENDING

SENT

FAILED

---

##################################################
# AUDIT DOMAIN
##################################################

TABLE: audit_logs

Purpose:
Audit seluruh aktivitas penting.

Columns:

id BIGSERIAL PK

user_id UUID FK users

entity_type VARCHAR(100)

entity_id VARCHAR(255)

action VARCHAR(100)

old_value JSONB

new_value JSONB

ip_address VARCHAR(100)

created_at TIMESTAMP

Indexes:

user_id

entity_type

action

created_at

---

Examples:

CREATE_STRATEGY

UPDATE_STRATEGY

DELETE_STRATEGY

OPEN_POSITION

CLOSE_POSITION

UPDATE_SETTINGS

---

##################################################
# SYSTEM DOMAIN
##################################################

TABLE: system_metrics

Purpose:
Monitoring performa sistem.

Columns:

id BIGSERIAL PK

metric_name VARCHAR(100)

metric_value NUMERIC

captured_at TIMESTAMP

Indexes:

metric_name

captured_at

---

Examples:

CPU_USAGE

MEMORY_USAGE

API_RESPONSE_TIME

DB_CONNECTIONS

---

TABLE: system_alerts

Purpose:
Alert internal sistem.

Columns:

id UUID PK

alert_type VARCHAR(100)

severity VARCHAR(20)

message TEXT

status VARCHAR(20)

created_at TIMESTAMP

resolved_at TIMESTAMP

Indexes:

alert_type

severity

status

created_at

---

Severity:

LOW

MEDIUM

HIGH

CRITICAL
