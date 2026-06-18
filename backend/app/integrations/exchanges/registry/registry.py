from __future__ import annotations

from typing import Any

from app.integrations.exchanges.interfaces import ExchangeAdapter
from app.integrations.exchanges.registry.capability import ExchangeCapabilityCatalog


class ExchangeAdapterRegistry:
    def __init__(self, adapters: dict[str, ExchangeAdapter] | None = None) -> None:
        self._adapters: dict[str, ExchangeAdapter] = {}
        self.capability_catalog = ExchangeCapabilityCatalog()
        if adapters:
            for key, adapter in adapters.items():
                self.register(key, adapter)
        elif adapters is None:
            self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        from app.integrations.exchanges.binance import BinanceAdapter

        self.register("binance", BinanceAdapter(testnet=True))

    def register(self, key: str, adapter: ExchangeAdapter) -> None:
        normalized_keys = self._keys_for(key)
        for normalized_key in normalized_keys:
            self._adapters[normalized_key] = adapter

    def get(self, key: str) -> ExchangeAdapter | None:
        for normalized_key in self._keys_for(key):
            adapter = self._adapters.get(normalized_key)
            if adapter is not None:
                return adapter
        return None

    def require(self, key: str) -> ExchangeAdapter:
        adapter = self.get(key)
        if adapter is None:
            raise KeyError(f"No exchange adapter registered for {key}")
        return adapter

    def keys(self) -> list[str]:
        return sorted(set(self._adapters))

    @staticmethod
    def _keys_for(key: str) -> list[str]:
        normalized = key.strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {normalized}
        if normalized == "binance":
            aliases.update({"binance_spot", "SPOT"})
        if normalized == "interactive_brokers":
            aliases.update({"ibkr", "interactive brokers", "interactive_broker"})
        if normalized == "okx":
            aliases.update({"okex"})
        return [key.lower() for key in sorted(aliases, key=len, reverse=True)]


class ExchangeAdapterFactory:
    def __init__(self, registry: ExchangeAdapterRegistry | None = None) -> None:
        self.registry = registry or ExchangeAdapterRegistry()
        self._builders: dict[str, Any] = {}

    def register_builder(self, key: str, builder: Any) -> None:
        self._builders[key] = builder

    def create(self, key: str, **kwargs: Any) -> ExchangeAdapter:
        builder = self._builders.get(key) or self._builders.get(self._normalize_key(key))
        if builder is None:
            adapter = self.registry.get(key)
            if adapter is None:
                raise KeyError(f"No exchange adapter registered for {key}")
            return adapter

        adapter = builder(**kwargs)
        self.registry.register(key, adapter)
        return adapter

    @staticmethod
    def _normalize_key(key: str) -> str:
        return key.strip().lower().replace(" ", "_").replace("-", "_")
