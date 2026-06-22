"""Result pattern package."""

from __future__ import annotations

from .result import Err, Ok, Result, failure, is_err, is_ok, success, unwrap

__all__ = ["Err", "Ok", "Result", "failure", "is_err", "is_ok", "success", "unwrap"]
