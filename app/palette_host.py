"""FastCommandCenter palette host — serves favorites as a live text provider.

Runs only palette-managed (fasttool.json launches the exe with --palette):
keeps a hidden FastToolIPC window open via the fasttool_palette shim and
answers each typed query with frecency-sorted favorite paths. FCC owns what
happens on selection (clipboard + paste) and never reports the pick back, so
usage counts only grow through normal CLI use.
"""

from __future__ import annotations

import logging
import time

from fasttool_palette import FastToolPalette, TextSuggestion, palette_mode

from app.cli._common import EXIT_USAGE
from app.config.settings import Settings
from app.constants import LOG_NAME
from app.favorites.filter import match
from app.favorites.path_resolver import resolve
from app.favorites.repository import FavoritesRepository
from app.favorites.usage import UsageStore
from app.logging_setup import configure_logging

TOOL_ID = "clifavorites"
PROVIDER_ID = "folders"
POLL_INTERVAL_S = 0.05

log = logging.getLogger(LOG_NAME)


def build_suggestions(query: str, settings: Settings) -> list[TextSuggestion]:
    """One palette query -> frecency-sorted suggestions.

    Reloads the favorites/usage files on every call so fav-add/fav-del edits
    show without restarting the tool.
    """
    favorites = FavoritesRepository(settings.favorites_path).load()
    ranked = UsageStore(settings.usage_path).sort(match(favorites, query))
    return [
        TextSuggestion(title=fav.name, text=str(resolve(fav.raw_path)), subtitle=fav.raw_path)
        for fav in ranked
    ]


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    if not palette_mode():
        log.error("this binary only runs palette-managed by FastCommandCenter (pass --palette)")
        return EXIT_USAGE
    palette = FastToolPalette(TOOL_ID)
    palette.add_text_provider(
        PROVIDER_ID, lambda query, _session_id: build_suggestions(query, settings)
    )
    log.info("palette host running (tool_id=%s, favorites=%s)", TOOL_ID, settings.favorites_path)
    while True:
        palette.poll()
        time.sleep(POLL_INTERVAL_S)
