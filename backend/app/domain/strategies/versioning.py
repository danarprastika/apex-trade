from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, version: str) -> "SemanticVersion":
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError("Version must follow MAJOR.MINOR.PATCH")
        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
        except ValueError as exc:
            raise ValueError("Version must contain only integers") from exc
        if major < 0 or minor < 0 or patch < 0:
            raise ValueError("Version parts must be non-negative")
        return cls(major=major, minor=minor, patch=patch)

    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        return self.major == other.major

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
