"""Centralized environment-driven settings for cli-favorites."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.constants import (
    ENV_FAVORITES_PATH,
    ENV_LOG_LEVEL,
    FAVORITES_FILENAME,
    USAGE_FILENAME_SUFFIX,
)

DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class Settings:
    favorites_path: Path
    usage_path: Path
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        raw = os.getenv(ENV_FAVORITES_PATH)
        favorites_path = Path(raw) if raw else Path.home() / FAVORITES_FILENAME
        usage_path = favorites_path.with_name(favorites_path.name + USAGE_FILENAME_SUFFIX)
        return cls(
            favorites_path=favorites_path,
            usage_path=usage_path,
            log_level=os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
        )
