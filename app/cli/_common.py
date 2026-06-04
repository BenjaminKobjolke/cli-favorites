"""Shared exit codes and bootstrapping for CLI entry points."""

from __future__ import annotations

import logging

from app.config.settings import Settings
from app.constants import LOG_NAME
from app.favorites.repository import FavoritesRepository
from app.favorites.usage import UsageStore
from app.logging_setup import configure_logging
from app.ui.colors import init_color

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def bootstrap() -> tuple[Settings, FavoritesRepository, UsageStore, logging.Logger]:
    """Configure logging + color and return (settings, repository, usage, logger)."""
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    init_color()
    repo = FavoritesRepository(settings.favorites_path)
    usage = UsageStore(settings.usage_path)
    log = logging.getLogger(LOG_NAME)
    return settings, repo, usage, log
