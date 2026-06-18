from __future__ import annotations

import ast
import time
from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation, SignalResult, SignalType, StrategyMetadata


class CustomSandboxPlugin(StrategyPlugin):
    _ALLOWED_IMPORTS = {"math"}
    _FORBIDDEN_NAMES = {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__import__",
        "breakpoint",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "memoryview",
    }
    _FORBIDDEN_ATTRIBUTES = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "requests",
        "http",
        "urllib",
        "pathlib",
        "shutil",
        "tempfile",
        "multiprocessing",
        "threading",
        "asyncio",
        "importlib",
    }

    def __init__(self, code: str = "custom") -> None:
        self._config: dict[str, Any] = {}
        self._code = code
        self._user_code: str = ""
        self._compiled_code: Any = None
        self._max_execution_ms: int = 100

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name=f"Custom: {self._code}",
            version="1.0.0",
            strategy_type=StrategyType.custom,
            description="User-defined custom strategy",
            author="User",
            min_lookback_periods=10,
            supported_assets=["*"],
            supported_timeframes=["*"],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        validation = self.validate_config(config)
        if not validation.valid:
            raise ValueError(validation.errors)
        self._config = config
        self._user_code = str(config["custom_code"])
        self._max_execution_ms = int(config.get("max_execution_ms", self._max_execution_ms))
        self._compiled_code = compile(self._user_code, f"<custom-strategy-{self._code}>", "exec")

    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        errors: list[str] = []
        custom_code = config.get("custom_code")
        if not isinstance(custom_code, str) or not custom_code.strip():
            errors.append("custom_code is required for custom strategies")
        if "max_execution_ms" in config:
            if not isinstance(config["max_execution_ms"], int) or config["max_execution_ms"] <= 0:
                errors.append("max_execution_ms must be a positive integer")
        if custom_code and isinstance(custom_code, str):
            errors.extend(self._validate_source(custom_code))
        return ConfigValidation(valid=len(errors) == 0, errors=errors)

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "custom_code": {
                    "type": "string",
                    "description": "Python code defining a single apex_strategy(market_data) function",
                },
                "max_execution_ms": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 100,
                    "description": "Maximum allowed execution time per analyze call",
                },
            },
            "required": ["custom_code"],
        }

    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        if not self._compiled_code:
            return None
        started_at = time.perf_counter()
        safe_globals: dict[str, Any] = {"__builtins__": {}}
        local_scope: dict[str, Any] = {}
        try:
            exec(self._compiled_code, safe_globals, local_scope)
            strategy_function = local_scope.get("apex_strategy")
            if not callable(strategy_function):
                raise ValueError("custom code must define apex_strategy(market_data)")
            result = strategy_function(market_data)
            duration_ms = (time.perf_counter() - started_at) * 1000
            if duration_ms > self._max_execution_ms:
                raise TimeoutError("custom strategy exceeded max_execution_ms")
            return self._normalize_result(result)
        except Exception:
            raise

    def _validate_source(self, source: str) -> list[str]:
        errors: list[str] = []
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return [f"custom_code syntax error: {exc}"]

        visitor = _SecurityVisitor(self._ALLOWED_IMPORTS, self._FORBIDDEN_NAMES, self._FORBIDDEN_ATTRIBUTES)
        visitor.visit(tree)
        errors.extend(visitor.errors)
        if "apex_strategy" not in visitor.functions:
            errors.append("custom_code must define apex_strategy(market_data)")
        return errors

    def _normalize_result(self, result: Any) -> SignalResult | None:
        if result is None:
            return None
        if not isinstance(result, dict):
            raise ValueError("apex_strategy must return a dict or None")
        signal_type = str(result.get("signal_type", "")).upper()
        if signal_type not in {member.value for member in SignalType}:
            raise ValueError("signal_type must be BUY, SELL, or HOLD")
        confidence = float(result.get("confidence", 0.0))
        entry_price = float(result.get("entry_price", 0.0))
        if confidence < 0 or confidence > 100:
            raise ValueError("confidence must be between 0 and 100")
        if entry_price <= 0:
            raise ValueError("entry_price must be greater than zero")
        reason = str(result.get("reason", "Custom strategy signal"))
        stop_loss = result.get("stop_loss")
        take_profit = result.get("take_profit")
        return SignalResult(
            signal_type=SignalType(signal_type),
            confidence=confidence,
            reason=reason,
            entry_price=entry_price,
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None,
            metadata=result.get("metadata", {}),
        )


class _SecurityVisitor(ast.NodeVisitor):
    def __init__(
        self,
        allowed_imports: set[str],
        forbidden_names: set[str],
        forbidden_attributes: set[str],
    ) -> None:
        self.allowed_imports = allowed_imports
        self.forbidden_names = forbidden_names
        self.forbidden_attributes = forbidden_attributes
        self.errors: list[str] = []
        self.functions: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root not in self.allowed_imports:
                self.errors.append(f"import {alias.name} is not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".")[0]
        if root not in self.allowed_imports:
            self.errors.append(f"import {node.module} is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in self.forbidden_names:
            self.errors.append(f"call to {node.func.id} is not allowed")
        if isinstance(node.func, ast.Attribute) and node.func.attr in self.forbidden_attributes:
            self.errors.append(f"attribute {node.func.attr} is not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.forbidden_attributes:
            self.errors.append(f"attribute {node.attr} is not allowed")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.add(node.name)
        self.generic_visit(node)
