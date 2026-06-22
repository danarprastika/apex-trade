"""Result status enumeration."""

from __future__ import annotations

from enum import StrEnum


class ResultStatus(StrEnum):
    """Result operation status values."""

    SUCCESS = "success"
    FAILURE = "failure"


__all__ = ["ResultStatus"]
