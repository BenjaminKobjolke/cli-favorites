"""Sidecar usage store — frecency tracking for favorites.

Stores, next to the favorites file, a JSON map of ``"name|raw_path"`` ->
``{"count": int, "last_used": <epoch seconds>}``. Sorting layers a frecency
score (usage count weighted by recency of last use) on top of the filtered
candidate list without touching the favorites file format.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

from app.constants import (
    LOG_NAME,
    RECENCY_WEIGHT_DEFAULT,
    RECENCY_WEIGHTS,
)
from app.favorites.entry import Favorite
from app.io_utils import atomic_write_text

log = logging.getLogger(LOG_NAME)


def recency_weight(age_seconds: float) -> float:
    """Multiplier for a usage count based on how long ago it was last used."""
    for max_age, weight in RECENCY_WEIGHTS:
        if age_seconds < max_age:
            return weight
    return RECENCY_WEIGHT_DEFAULT


class UsageStore:
    def __init__(self, path: Path, now: Callable[[], float] | None = None) -> None:
        self._path = path
        self._now = now if now is not None else time.time
        self._data: dict[str, dict[str, float]] = self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> dict[str, dict[str, float]]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as err:
            log.debug("ignoring unreadable usage file %s: %s", self._path, err)
            return {}
        if not isinstance(raw, dict):
            log.debug("usage file %s is not a JSON object; ignoring", self._path)
            return {}
        return raw

    def _save(self) -> None:
        atomic_write_text(self._path, json.dumps(self._data, indent=2))

    def score(self, favorite: Favorite, now: float | None = None) -> float:
        entry = self._data.get(favorite.to_line())
        if not entry:
            return 0.0
        count = float(entry.get("count", 0))
        last_used = float(entry.get("last_used", 0.0))
        moment = self._now() if now is None else now
        return count * recency_weight(moment - last_used)

    def sort(self, favorites: list[Favorite]) -> list[Favorite]:
        """Return favorites ordered by frecency (desc). Stable: ties keep order."""
        moment = self._now()
        return sorted(favorites, key=lambda f: self.score(f, moment), reverse=True)

    def record(self, favorite: Favorite) -> None:
        """Increment usage count for ``favorite`` and stamp last-used = now."""
        key = favorite.to_line()
        entry = self._data.get(key, {})
        entry["count"] = float(entry.get("count", 0)) + 1
        entry["last_used"] = self._now()
        self._data[key] = entry
        self._save()

    def remove(self, favorite: Favorite) -> None:
        """Drop any usage record for ``favorite`` (used after delete)."""
        if self._data.pop(favorite.to_line(), None) is not None:
            self._save()
