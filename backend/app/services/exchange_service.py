from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ccxt
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_secret, encrypt_secret
from app.core.exceptions import NotFoundError, ValidationError
from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.repositories.exchange_repository import ExchangeAccountRepository, ExchangeRepository

logger = logging.getLogger(__name__)


class ExchangeService:
    def __init__(self, db: Session):
        self.db = db
        self.exchanges = ExchangeRepository(db)
        self.accounts = ExchangeAccountRepository(db)

    def create_exchange(self, name: str, exchange_type: str, status: str = "ACTIVE") -> Exchange:
        exchange = self.exchanges.create(name=name, exchange_type=exchange_type, status=status)
        self.exchanges.commit()
        self.exchanges.refresh(exchange)
        logger.info("Created exchange exchange_id=%s name=%s", exchange.id, exchange.name)
        return exchange

    def list_exchanges(self, limit: int = 100, offset: int = 0) -> list[Exchange]:
        return self.exchanges.list(limit=limit, offset=offset)

    def get_exchange(self, exchange_id: str) -> Exchange:
        exchange = self.exchanges.get(exchange_id)
        if not exchange:
            raise NotFoundError("Exchange not found")
        return exchange

    def create_account(self, user_id: str, exchange_id: str, api_key: str, api_secret: str, is_testnet: bool = False) -> ExchangeAccount:
        exchange = self.get_exchange(exchange_id)
        if not api_key or not api_secret:
            raise ValidationError("Exchange credentials are required")
        self._get_ccxt_class(exchange.exchange_type)

        account = self.accounts.create(
            user_id=user_id,
            exchange_id=exchange_id,
            api_key_encrypted=encrypt_secret(api_key),
            api_secret_encrypted=encrypt_secret(api_secret),
            is_testnet=is_testnet,
            status="ACTIVE",
        )
        self.accounts.commit()
        self.accounts.refresh(account)
        logger.info("Created exchange account account_id=%s user_id=%s exchange_id=%s", account.id, user_id, exchange_id)
        return account

    def list_accounts(self, user_id: str, limit: int = 100, offset: int = 0) -> list[ExchangeAccount]:
        return self.accounts.list_by_user(user_id, limit=limit, offset=offset)

    def get_account(self, account_id: str, user_id: str | None = None) -> ExchangeAccount:
        account = self.accounts.get(account_id) if user_id is None else self.accounts.get_by_user(user_id, account_id)
        if not account:
            raise NotFoundError("Exchange account not found")
        return account

    def decrypt_credentials(self, account: ExchangeAccount) -> tuple[str, str]:
        return decrypt_secret(account.api_key_encrypted), decrypt_secret(account.api_secret_encrypted)

    def test_connection(self, account_id: str, user_id: str) -> dict[str, str | bool]:
        account = self.get_account(account_id, user_id=user_id)
        exchange = self.get_exchange(account.exchange_id)
        client = self._build_client(exchange, account)
        logger.info("Testing exchange connection account_id=%s exchange_id=%s", account.id, account.exchange_id)
        try:
            client.load_markets()
            client.fetch_balance()
            account.status = "ACTIVE"
            account.sync_status = "VERIFIED"
            account.error_message = None
            self.accounts.commit()
            self.accounts.refresh(account)
            return {"account_id": account.id, "status": "ok", "verified": True}
        except Exception as exc:
            account.status = "ERROR"
            account.sync_status = "FAILED"
            account.error_message = str(exc)
            self.accounts.commit()
            self.accounts.refresh(account)
            raise ValidationError("Exchange connection test failed") from exc

    def sync_account(self, account_id: str, user_id: str) -> dict[str, Any]:
        account = self.get_account(account_id, user_id=user_id)
        exchange = self.get_exchange(account.exchange_id)
        client = self._build_client(exchange, account)
        logger.info("Synchronizing exchange account account_id=%s exchange_id=%s", account.id, account.exchange_id)
        try:
            client.load_markets()
            balance = self._normalize_balance(client.fetch_balance())
            positions = self._normalize_positions(getattr(client, "fetch_positions", lambda: [])())
            account.status = "ACTIVE"
            account.sync_status = "SYNCED"
            account.last_synced_at = datetime.now(timezone.utc)
            account.balance_snapshot = balance
            account.position_snapshot = positions
            account.error_message = None
            self.accounts.commit()
            self.accounts.refresh(account)
            return {
                "account_id": account.id,
                "status": "synced",
                "synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
                "balances": balance,
                "positions": positions,
            }
        except Exception as exc:
            account.status = "ERROR"
            account.sync_status = "FAILED"
            account.error_message = str(exc)
            self.accounts.commit()
            self.accounts.refresh(account)
            logger.exception("Exchange account sync failed account_id=%s", account.id)
            raise ValidationError("Exchange account sync failed") from exc

    def _build_client(self, exchange: Exchange, account: ExchangeAccount) -> ccxt.Exchange:
        exchange_class = self._get_ccxt_class(exchange.exchange_type)
        api_key, api_secret = self.decrypt_credentials(account)
        options: dict[str, Any] = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        }
        if account.is_testnet:
            options["sandbox"] = True
        client = exchange_class(options)
        if account.is_testnet and hasattr(client, "set_sandbox_mode"):
            client.set_sandbox_mode(True)
        return client

    @staticmethod
    def _get_ccxt_class(exchange_type: str) -> type[ccxt.Exchange]:
        normalized = exchange_type.strip().upper()
        class_name = normalized.lower()
        if not hasattr(ccxt, class_name):
            raise ValidationError(f"Unsupported exchange type: {exchange_type}")
        exchange_class = getattr(ccxt, class_name)
        if not issubclass(exchange_class, ccxt.Exchange):
            raise ValidationError(f"Unsupported exchange type: {exchange_type}")
        return exchange_class

    @staticmethod
    def _normalize_balance(balance: dict[str, Any]) -> dict[str, Any]:
        total = balance.get("total") or {}
        free = balance.get("free") or {}
        used = balance.get("used") or {}
        currencies = sorted(set(total) | set(free) | set(used))
        return {
            "timestamp": balance.get("timestamp"),
            "datetime": balance.get("datetime"),
            "currencies": [
                {
                    "currency": currency,
                    "free": free.get(currency, 0),
                    "used": used.get(currency, 0),
                    "total": total.get(currency, 0),
                }
                for currency in currencies
                if currency != "info"
            ],
        }

    @staticmethod
    def _normalize_positions(positions: Any) -> list[dict[str, Any]]:
        normalized_positions: list[dict[str, Any]] = []
        for position in positions or []:
            normalized_positions.append(
                {
                    "symbol": position.get("symbol"),
                    "side": position.get("side"),
                    "contracts": position.get("contracts"),
                    "entry_price": position.get("entryPrice"),
                    "mark_price": position.get("markPrice"),
                    "unrealized_pnl": position.get("unrealizedPnl"),
                    "leverage": position.get("leverage"),
                }
            )
        return normalized_positions
