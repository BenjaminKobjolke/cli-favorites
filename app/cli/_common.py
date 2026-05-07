"""Shared exit codes and bootstrapping for CLI entry points."""

from __future__ import annotations

import logging

from app.config.settings import Settings
from app.constants import LOG_NAME
from app.favorites.repository import FavoritesRepository
from app.logging_setup import configure_logging

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def bootstrap() -> tuple[Settings, FavoritesRepository, logging.Logger]:
    """Configure logging and return (settings, repository, logger)."""
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    repo = FavoritesRepository(settings.favorites_path)
    log = logging.getLogger(LOG_NAME)
    return settings, repo, log
