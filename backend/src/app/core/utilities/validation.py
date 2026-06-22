"""Validation helpers."""

from __future__ import annotations

from enum import Enum

from app.core.exceptions import ConfigurationError


def require_not_empty(value: str, *, field_name: str) -> str:
    """Return a non-empty string or raise ConfigurationError."""
    if not value.strip():
        raise ConfigurationError(
            message=f"{field_name} must not be empty",
            code="EMPTY_REQUIRED_VALUE",
            details={"field": field_name},
        )
    return value.strip()


def ensure_positive_int(value: int, *, field_name: str) -> int:
    """Return a positive integer or raise ConfigurationError."""
    if value <= 0:
        raise ConfigurationError(
            message=f"{field_name} must be positive",
            code="INVALID_POSITIVE_INT",
            details={"field": field_name, "value": value},
        )
    return value


def coerce_bool(value: bool | str | int) -> bool:
    """Coerce a common boolean representation."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigurationError(
        message="Value must be a boolean",
        code="INVALID_BOOLEAN",
        details={"value": value},
    )


def validate_enum_value[T: Enum](value: str, enum_type: type[T]) -> T:
    """Validate and return an enum value."""
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_type)
        raise ConfigurationError(
            message=f"Invalid value for {enum_type.__name__}",
            code="INVALID_ENUM_VALUE",
            details={"enum": enum_type.__name__, "value": value, "allowed": allowed},
        ) from exc


__all__ = [
    "ConfigurationError",
    "coerce_bool",
    "ensure_positive_int",
    "require_not_empty",
    "validate_enum_value",
]
