from __future__ import annotations

import json
import logging
from typing import Any, Callable

from app.core.exceptions import NotFoundError
from app.database.repositories.trading_repository import (
    StrategyParameterRepository,
    StrategyParameterSchemaRepository,
    StrategyRepository,
)
from app.domain.entities.strategy import StrategyStatus
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation
from app.domain.strategies.versioning import SemanticVersion
from app.services.plugin_registry import PluginRegistry
from plugins import get_builtin_plugins

logger = logging.getLogger(__name__)


class StrategyConfigManager:
    def __init__(self, strategy_repository: StrategyRepository, registry: PluginRegistry) -> None:
        self._repository = strategy_repository
        self._parameters = StrategyParameterRepository(strategy_repository.db)
        self._parameter_schemas = StrategyParameterSchemaRepository(strategy_repository.db)
        self._registry = registry
        self._plugin_cache: dict[str, StrategyPlugin] = {}

    def load_plugin(self, code: str) -> StrategyPlugin:
        if code in self._plugin_cache:
            return self._plugin_cache[code]

        plugin_classes = get_builtin_plugins()
        if code not in plugin_classes:
            raise NotFoundError(f"Strategy plugin not found: {code}")
        self._registry.mark_discovered(code)

        strategy = self._repository.get_by_code(code)
        if not strategy:
            raise NotFoundError(f"Strategy not found: {code}")
        self._require_active(strategy)

        plugin = plugin_classes[code]()
        self._registry.mark_loaded(code)
        validation = plugin.validate_config({})
        if not validation.valid:
            self._registry.mark_failed(code, "; ".join(validation.errors))
            raise ValueError(f"Invalid default configuration: {validation.errors}")
        self._registry.mark_validated(code)

        params = self._load_parameters(code)
        validation = plugin.validate_config(params)
        if not validation.valid:
            self._registry.mark_failed(code, "; ".join(validation.errors))
            raise ValueError(f"Invalid configuration: {validation.errors}")

        self._validate_plugin_version(strategy.version, plugin.metadata.version)
        plugin.initialize(params)
        self._plugin_cache[code] = plugin
        self._registry.register(plugin)
        self._registry.mark_initialized(code)
        self._registry.activate(code)
        logger.info("Loaded strategy plugin code=%s version=%s", code, plugin.metadata.version)
        return plugin

    def get_parameters_schema(self, code: str, persist: bool = True) -> dict[str, Any]:
        plugin_classes = get_builtin_plugins()
        if code not in plugin_classes:
            raise NotFoundError(f"Strategy plugin not found: {code}")

        plugin = plugin_classes[code]()
        schema = plugin.get_parameters_schema()
        if persist:
            self.save_parameter_schema(code, plugin.metadata.version)
        return schema

    def get_saved_parameter_schema(self, code: str) -> dict[str, Any] | None:
        strategy = self._repository.get_by_code(code)
        if not strategy:
            raise NotFoundError(f"Strategy not found: {code}")
        schema = self._parameter_schemas.get_active(strategy.id)
        return schema.parameters_schema if schema else None

    def validate_parameters(self, code: str, params: dict[str, Any]) -> ConfigValidation:
        plugin_classes = get_builtin_plugins()
        if code not in plugin_classes:
            return ConfigValidation(valid=False, errors=[f"Unknown strategy: {code}"])

        plugin = plugin_classes[code]()
        return plugin.validate_config(params)

    def update_parameters(self, code: str, params: dict[str, Any]) -> None:
        validation = self.validate_parameters(code, params)
        if not validation.valid:
            raise ValueError(f"Invalid parameters: {validation.errors}")

        strategy = self._repository.get_by_code(code)
        if not strategy:
            raise NotFoundError(f"Strategy not found: {code}")
        self._parameters.delete_by_strategy(strategy.id)
        for name, value in params.items():
            self._parameters.create(
                strategy_id=strategy.id,
                parameter_name=str(name),
                parameter_value=self._serialize_parameter(value),
            )
        self._parameters.commit()
        self.clear_cache(code)
        logger.info("Updated parameters for strategy code=%s count=%s", code, len(params))

    def save_parameter_schema(self, code: str, version: str, migrated_from: str | None = None) -> dict[str, Any]:
        strategy = self._repository.get_by_code(code)
        if not strategy:
            raise NotFoundError(f"Strategy not found: {code}")
        schema = self.get_parameters_schema(code, persist=False)
        existing = self._parameter_schemas.get_by_version(strategy.id, version)
        if existing:
            return existing.parameters_schema

        self._parameter_schemas.deactivate_previous(strategy.id)
        saved_schema = self._parameter_schemas.create(
            strategy_id=strategy.id,
            version=version,
            parameters_schema=schema,
            migrated_from=migrated_from,
            is_active=True,
        )
        self._parameter_schemas.commit()
        logger.info("Saved strategy parameter schema code=%s version=%s", code, version)
        return saved_schema.parameters_schema

    def migrate_parameters(
        self,
        code: str,
        from_version: str,
        to_version: str,
        params: dict[str, Any],
        allow_major_migration: bool = False,
        migration_rules: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from_semver = SemanticVersion.parse(from_version)
        to_semver = SemanticVersion.parse(to_version)
        if from_semver.major != to_semver.major and not allow_major_migration:
            raise ValueError("Major strategy version migration requires explicit approval")
        if from_semver > to_semver:
            raise ValueError("Cannot migrate parameters to an older strategy version")

        migrated_params = dict(params)
        rules = migration_rules or {}
        for target_name, rule in rules.items():
            if callable(rule):
                migrated_params[target_name] = rule(migrated_params)
            elif target_name not in migrated_params:
                migrated_params[target_name] = rule

        plugin_classes = get_builtin_plugins()
        if code not in plugin_classes:
            raise NotFoundError(f"Strategy plugin not found: {code}")
        validation = plugin_classes[code]().validate_config(migrated_params)
        if not validation.valid:
            raise ValueError(f"Migrated parameters are invalid: {validation.errors}")
        logger.info(
            "Migrated strategy parameters code=%s from=%s to=%s",
            code,
            from_version,
            to_version,
        )
        return migrated_params

    def _load_parameters(self, code: str) -> dict[str, Any]:
        strategy = self._repository.get_by_code(code)
        if not strategy:
            raise NotFoundError(f"Strategy not found: {code}")
        params: dict[str, Any] = {}
        for parameter in self._parameters.find_by_strategy(strategy.id):
            params[parameter.parameter_name] = self._deserialize_parameter(parameter.parameter_value)
        return params

    def _validate_plugin_version(self, strategy_version: str, plugin_version: str) -> None:
        strategy_semver = SemanticVersion.parse(strategy_version)
        plugin_semver = SemanticVersion.parse(plugin_version)
        if not plugin_semver.is_compatible_with(strategy_semver):
            raise ValueError(
                f"Strategy plugin version {plugin_version} is incompatible with strategy version {strategy_version}"
            )

    def _require_active(self, strategy: Any) -> None:
        if strategy.status != StrategyStatus.active.value:
            raise ValueError(f"Strategy is not active: {strategy.code}")

    def _serialize_parameter(self, value: Any) -> str:
        if isinstance(value, (dict, list, int, float, bool)) or value is None:
            return json.dumps(value)
        return str(value)

    def _deserialize_parameter(self, value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def clear_cache(self, code: str | None = None) -> None:
        if code:
            self._plugin_cache.pop(code, None)
        else:
            self._plugin_cache.clear()
