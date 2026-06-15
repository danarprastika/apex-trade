from __future__ import annotations

from base64 import urlsafe_b64encode
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken
from pydantic import SecretStr

from app.core.config import settings
from app.core.exceptions import ValidationError


class SecretEncryptionError(RuntimeError):
    pass


def _build_key(raw_key: str) -> bytes:
    raw_bytes = raw_key.encode("utf-8")
    if len(raw_bytes) == 32:
        return raw_bytes
    return urlsafe_b64encode(sha256(raw_bytes).digest())


def encrypt_secret(value: str | SecretStr) -> str:
    secret_value = value.get_secret_value() if isinstance(value, SecretStr) else value
    if not secret_value:
        raise ValidationError("Secret value cannot be empty")
    try:
        return Fernet(_build_key(settings.encryption_key)).encrypt(secret_value.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise SecretEncryptionError("Unable to encrypt secret") from exc


def decrypt_secret(value: str) -> str:
    try:
        return Fernet(_build_key(settings.encryption_key)).decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise SecretEncryptionError("Unable to decrypt secret") from exc
