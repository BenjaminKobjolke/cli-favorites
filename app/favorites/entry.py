"""Favorite entry — represents one line from the favorites file."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.constants import FIELD_SEPARATOR, SCOPE_BOTH, SCOPE_NAME, SCOPE_PATH


class InvalidFavoriteError(ValueError):
    """Raised when a favorite line/name/path is malformed."""


class SearchScope(Enum):
    """Which field(s) of a favorite the filter searches."""

    NAME = SCOPE_NAME
    PATH = SCOPE_PATH
    BOTH = SCOPE_BOTH


@dataclass(frozen=True)
class Favorite:
    name: str
    raw_path: str

    def to_line(self) -> str:
        return f"{self.name}{FIELD_SEPARATOR}{self.raw_path}"

    def searchable_fields(self, scope: SearchScope = SearchScope.BOTH) -> list[str]:
        """Field values the filter searches. Add a field here to make it searchable."""
        if scope is SearchScope.NAME:
            return [self.name]
        if scope is SearchScope.PATH:
            return [self.raw_path]
        return [self.name, self.raw_path]

    @classmethod
    def from_line(cls, line: str) -> Favorite:
        stripped = line.rstrip("\r\n")
        if FIELD_SEPARATOR not in stripped:
            raise InvalidFavoriteError(f"missing '{FIELD_SEPARATOR}' separator: {line!r}")
        name, raw_path = stripped.split(FIELD_SEPARATOR, 1)
        name = name.strip()
        raw_path = raw_path.strip()
        if not name or not raw_path:
            raise InvalidFavoriteError(f"empty name or path: {line!r}")
        return cls(name=name, raw_path=raw_path)


def validate_name(name: str) -> str:
    """Strip and validate a name. Raise InvalidFavoriteError if illegal."""
    cleaned = name.strip()
    if not cleaned:
        raise InvalidFavoriteError("name must not be empty")
    if FIELD_SEPARATOR in cleaned:
        raise InvalidFavoriteError(f"name must not contain '{FIELD_SEPARATOR}'")
    if "\n" in cleaned or "\r" in cleaned:
        raise InvalidFavoriteError("name must not contain newline characters")
    return cleaned
