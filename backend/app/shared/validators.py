from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_URL_RE = re.compile(r"^https?://[^\s]+$")


def validate_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value))


def validate_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(value))


def validate_url(value: str) -> bool:
    return bool(_URL_RE.match(value))
