from __future__ import annotations

from enum import Enum


class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    STOCK = "STOCK"
    ETF = "ETF"
    INDEX = "INDEX"
    FUTURES = "FUTURES"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class TimeInForce(str, Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    GTD = "GTD"


class ExchangeErrorCategory(str, Enum):
    CONFIGURATION = "CONFIGURATION"
    CREDENTIAL = "CREDENTIAL"
    VALIDATION = "VALIDATION"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK = "NETWORK"
    TEMPORARY_EXCHANGE = "TEMPORARY_EXCHANGE"
    UNKNOWN_ORDER_STATE = "UNKNOWN_ORDER_STATE"
    RECONCILIATION = "RECONCILIATION"
    FAILOVER = "FAILOVER"
