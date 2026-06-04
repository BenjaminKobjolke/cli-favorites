"""Favorite entry — represents one line from the favorites file."""

from __future__ import annotations

from dataclasses import dataclass

from app.constants import FIELD_SEPARATOR


class InvalidFavoriteError(ValueError):
    """Raised when a favorite line/name/path is malformed."""


@dataclass(frozen=True)
class Favorite:
    name: str
    raw_path: str

    def to_line(self) -> str:
        return f"{self.name}{FIELD_SEPARATOR}{self.raw_path}"

    def searchable_fields(self) -> list[str]:
        """Field values the filter searches. Add a field here to make it searchable."""
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
