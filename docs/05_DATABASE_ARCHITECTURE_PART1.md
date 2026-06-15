# APEX Financial Intelligence Platform

Version: 0.1
Status: Draft
Document Type: Database Architecture

---

# 1. Purpose

Dokumen ini mendefinisikan:

- Database Architecture
- Entity Relationships
- Naming Conventions
- Data Lifecycle
- Future Expansion Strategy

Database harus mendukung:

Stage 1
Foundation Platform

Stage 2
Professional Platform

Stage 3
AI Platform

Stage 4
Autonomous Financial Ecosystem

---

# 2. Database Technology

Development:

SQLite

Production:

PostgreSQL

Future:

PostgreSQL Cluster

---

# 3. Database Design Principles

## Principle 1

Single Source Of Truth

Tidak boleh ada data duplikat.

---

## Principle 2

Auditability

Semua aktivitas penting harus dapat dilacak.

---

## Principle 3

Scalability

Mendukung pertumbuhan hingga jutaan candle.

---

## Principle 4

Modularity

Setiap domain memiliki tabel sendiri.

---

## Principle 5

Future Ready

Kompatibel dengan AI dan Multi-Agent System.

---

# 4. Schema Structure

Core Schemas:

identity
exchange
market
trading
portfolio
risk
system

Future Schemas:

intelligence
ai
research
knowledge

---

##################################################
# IDENTITY DOMAIN
##################################################

TABLE: users

Purpose:
Menyimpan akun pengguna.

Columns:

id UUID PK

username VARCHAR(50) UNIQUE

email VARCHAR(255) UNIQUE

password_hash TEXT

role VARCHAR(20)

status VARCHAR(20)

created_at TIMESTAMP

updated_at TIMESTAMP

Indexes:

username

email

status

---

TABLE: user_settings

Purpose:
Konfigurasi pengguna.

Columns:

id UUID PK

user_id UUID FK users

timezone VARCHAR(50)

language VARCHAR(20)

theme VARCHAR(20)

telegram_chat_id VARCHAR(100)

created_at TIMESTAMP

updated_at TIMESTAMP

Indexes:

user_id

---

##################################################
# EXCHANGE DOMAIN
##################################################

TABLE: exchanges

Purpose:
Daftar exchange.

Columns:

id UUID PK

name VARCHAR(50)

exchange_type VARCHAR(50)

status VARCHAR(20)

created_at TIMESTAMP

---

Example:

Binance

Bybit

OKX

---

TABLE: exchange_accounts

Purpose:
Koneksi akun user ke exchange.

Columns:

id UUID PK

user_id UUID FK

exchange_id UUID FK

api_key_encrypted TEXT

api_secret_encrypted TEXT

is_testnet BOOLEAN

status VARCHAR(20)

created_at TIMESTAMP

Indexes:

user_id

exchange_id

---

##################################################
# MARKET DOMAIN
##################################################

TABLE: assets

Purpose:
Master asset.

Columns:

id UUID PK

symbol VARCHAR(30)

name VARCHAR(100)

asset_type VARCHAR(30)

status VARCHAR(20)

Indexes:

symbol

asset_type

---

Examples:

BTC

ETH

SOL

XAU

EUR

---

TABLE: market_pairs

Purpose:
Pasangan perdagangan.

Columns:

id UUID PK

exchange_id UUID FK

base_asset_id UUID FK

quote_asset_id UUID FK

symbol VARCHAR(50)

status VARCHAR(20)

Indexes:

symbol

exchange_id

---

Example:

BTCUSDT

ETHUSDT

SOLUSDT

---

TABLE: candles

Purpose:
Data OHLCV.

Columns:

id BIGSERIAL PK

market_pair_id UUID FK

timeframe VARCHAR(10)

open NUMERIC

high NUMERIC

low NUMERIC

close NUMERIC

volume NUMERIC

open_time TIMESTAMP

close_time TIMESTAMP

Indexes:

market_pair_id

timeframe

open_time

Composite Index:

market_pair_id + timeframe + open_time

---

Retention Strategy:

Never Delete

Historical Asset

---

TABLE: order_book_snapshots

Purpose:
Snapshot orderbook.

Columns:

id BIGSERIAL PK

market_pair_id UUID FK

bid_volume NUMERIC

ask_volume NUMERIC

spread NUMERIC

captured_at TIMESTAMP

Indexes:

market_pair_id

captured_at

---

TABLE: funding_rates

Purpose:
Funding data futures.

Columns:

id BIGSERIAL PK

market_pair_id UUID FK

funding_rate NUMERIC

captured_at TIMESTAMP

Indexes:

market_pair_id

captured_at

---

TABLE: open_interest_records

Purpose:
Open interest history.

Columns:

id BIGSERIAL PK

market_pair_id UUID FK

open_interest NUMERIC

captured_at TIMESTAMP

Indexes:

market_pair_id

captured_at
