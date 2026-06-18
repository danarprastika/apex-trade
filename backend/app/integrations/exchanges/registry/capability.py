from __future__ import annotations

from app.domain.exchange.models import ExchangeCapability


class ExchangeCapabilityCatalog:
    def __init__(self) -> None:
        self._capabilities: dict[str, ExchangeCapability] = {
            "binance": ExchangeCapability(
                exchange_id="binance",
                exchange_name="Binance",
                asset_classes=("CRYPTO",),
                spot=True,
                margin=False,
                futures=False,
                order_book=True,
                funding_rate=False,
                open_interest=False,
                submit_order=False,
                cancel_order=False,
                modify_order=False,
                fetch_order=False,
                fetch_positions=False,
                fetch_balances=True,
                supported_order_types=("MARKET", "LIMIT"),
                supported_time_in_force=("GTC",),
            ),
            "bybit": ExchangeCapability(
                exchange_id="bybit",
                exchange_name="Bybit",
                asset_classes=("CRYPTO",),
                spot=True,
                futures=True,
                order_book=True,
                funding_rate=True,
                open_interest=True,
                submit_order=False,
                cancel_order=False,
                modify_order=False,
                fetch_order=False,
                fetch_positions=False,
                fetch_balances=True,
                supported_order_types=("MARKET", "LIMIT"),
                supported_time_in_force=("GTC",),
            ),
            "okx": ExchangeCapability(
                exchange_id="okx",
                exchange_name="OKX",
                asset_classes=("CRYPTO",),
                spot=True,
                futures=True,
                order_book=True,
                funding_rate=True,
                open_interest=True,
                submit_order=False,
                cancel_order=False,
                modify_order=False,
                fetch_order=False,
                fetch_positions=False,
                fetch_balances=True,
                supported_order_types=("MARKET", "LIMIT"),
                supported_time_in_force=("GTC",),
            ),
            "kucoin": ExchangeCapability(
                exchange_id="kucoin",
                exchange_name="KuCoin",
                asset_classes=("CRYPTO",),
                spot=True,
                order_book=True,
                submit_order=False,
                cancel_order=False,
                modify_order=False,
                fetch_order=False,
                fetch_positions=False,
                fetch_balances=True,
                supported_order_types=("MARKET", "LIMIT"),
                supported_time_in_force=("GTC",),
            ),
            "kraken": ExchangeCapability(
                exchange_id="kraken",
                exchange_name="Kraken",
                asset_classes=("CRYPTO", "FOREX"),
                spot=True,
                order_book=True,
                submit_order=False,
                cancel_order=False,
                modify_order=False,
                fetch_order=False,
                fetch_positions=False,
                fetch_balances=True,
                supported_order_types=("MARKET", "LIMIT"),
                supported_time_in_force=("GTC",),
            ),
            "interactive_brokers": ExchangeCapability(
                exchange_id="interactive_brokers",
                exchange_name="Interactive Brokers",
                asset_classes=("STOCK", "ETF", "FOREX", "INDEX", "FUTURES"),
                spot=False,
                stocks=True,
                forex=True,
                futures=True,
                order_book=False,
                submit_order=False,
                cancel_order=False,
                modify_order=False,
                fetch_order=False,
                fetch_positions=True,
                fetch_balances=True,
                supported_order_types=("MARKET", "LIMIT"),
                supported_time_in_force=("DAY", "GTC"),
            ),
        }

    def get(self, exchange_key: str) -> ExchangeCapability | None:
        normalized = self._normalize_key(exchange_key)
        return self._capabilities.get(normalized)

    def list(self) -> list[ExchangeCapability]:
        return list(self._capabilities.values())

    @staticmethod
    def _normalize_key(exchange_key: str) -> str:
        return exchange_key.strip().lower().replace(" ", "_").replace("-", "_")
