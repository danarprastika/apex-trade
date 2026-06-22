"""Secret resolution helpers for environment and Docker secret files."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from app.core.exceptions.configuration import SecretNotFoundError
from app.shared.types import JsonDict


class SecretResolver:
    """Resolve secrets from environment variables or mounted secret files."""

    env_key_prefix: ClassVar[str] = "QUANTX_"

    @classmethod
    def resolve(
        cls,
        name: str,
        *,
        default: str | None = None,
        secret_path: str | Path | None = None,
        required: bool = False,
    ) -> str | None:
        """Resolve a secret by name.

        The resolver checks an environment variable, then a Docker secret file,
        then the provided default value.
        """
        env_value = cls._resolve_from_environment(name)
        if env_value is not None:
            return env_value

        resolved_path = Path(secret_path) if isinstance(secret_path, str) else secret_path
        file_value = cls._resolve_from_file(resolved_path or Path("/run/secrets") / name)
        if file_value is not None:
            return file_value

        if default is not None:
            return default

        if required:
            raise SecretNotFoundError(name=name)

        return None

    @staticmethod
    def _resolve_from_environment(name: str) -> str | None:
        """Read a secret from the environment."""
        import os

        env_name = f"{SecretResolver.env_key_prefix}{name.upper()}"
        value = os.getenv(env_name)
        if value is None or not value.strip():
            return None
        return value.strip()

    @staticmethod
    def _resolve_from_file(path: Path | None) -> str | None:
        """Read a secret from a file."""
        if path is None or not path.exists() or not path.is_file():
            return None
        value = path.read_text(encoding="utf-8").strip()
        if not value:
            return None
        return value

    @classmethod
    def to_context(cls, name: str, value: str | None) -> JsonDict:
        """Return sanitized context for secret resolution logs."""
        return {
            "secret_name": name,
            "secret_present": value is not None,
            "secret_length": len(value) if value is not None else 0,
        }


__all__ = ["SecretResolver"]
