"""Read/write favorites file. Atomic writes via temp + replace."""

from __future__ import annotations

import logging
from pathlib import Path

from app.constants import LOG_NAME
from app.favorites.entry import Favorite, InvalidFavoriteError
from app.io_utils import atomic_write_text

log = logging.getLogger(LOG_NAME)


class FavoritesRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[Favorite]:
        if not self._path.exists():
            return []
        favorites: list[Favorite] = []
        text = self._read_text_with_fallback()
        for lineno, raw in enumerate(text.splitlines(), start=1):
            if not raw.strip():
                continue
            try:
                favorites.append(Favorite.from_line(raw))
            except InvalidFavoriteError as err:
                log.debug("skipping line %d in %s: %s", lineno, self._path, err)
        return favorites

    def save(self, favorites: list[Favorite]) -> None:
        body = "\n".join(fav.to_line() for fav in favorites)
        if body:
            body += "\n"
        atomic_write_text(self._path, body)

    def append(self, favorite: Favorite) -> None:
        existing = self.load()
        existing.append(favorite)
        self.save(existing)

    def remove_at(self, index: int) -> Favorite:
        existing = self.load()
        if index < 0 or index >= len(existing):
            raise IndexError(f"favorite index out of range: {index}")
        removed = existing.pop(index)
        self.save(existing)
        return removed

    def _read_text_with_fallback(self) -> str:
        """Read favorites file. Try UTF-8 first, fall back to cp1252 (Windows legacy)."""
        data = self._path.read_bytes()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            log.debug(
                "favorites file %s is not valid UTF-8; decoding as cp1252",
                self._path,
            )
            return data.decode("cp1252")
