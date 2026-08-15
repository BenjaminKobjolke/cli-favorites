"""Persistent user preferences sidecar (``<favorites>.config``, JSON)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.constants import CONFIG_KEY_MAX_RESULTS, DEFAULT_MAX_RESULTS
from app.io_utils import atomic_write_text


@dataclass(frozen=True)
class UserConfig:
    max_results: int = DEFAULT_MAX_RESULTS

    @classmethod
    def load(cls, path: Path) -> UserConfig:
        """Missing, corrupt, or invalid config falls back to defaults."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        raw = data.get(CONFIG_KEY_MAX_RESULTS) if isinstance(data, dict) else None
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 1:
            return cls()
        return cls(max_results=raw)

    def save(self, path: Path) -> None:
        atomic_write_text(path, json.dumps({CONFIG_KEY_MAX_RESULTS: self.max_results}))
