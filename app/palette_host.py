"""FastCommandCenter palette host — serves favorites as a live text provider.

Runs only palette-managed (fasttool.json launches the exe with --palette):
keeps a hidden FastToolIPC window open via the fasttool_palette shim and
answers each typed query with frecency-sorted favorite paths. FCC owns what
happens on selection (clipboard + paste); its fire-and-forget `selected`
echo is used here to bump the same frecency counts CLI use writes.
"""

from __future__ import annotations

import logging
import time

from fasttool_palette import FastToolPalette, TextSuggestion, palette_mode

from app.cli._common import EXIT_USAGE
from app.config.settings import Settings
from app.config.user_config import UserConfig
from app.constants import LOG_NAME
from app.favorites.entry import Favorite
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
    ranked = ranked[: UserConfig.load(settings.config_path).max_results]
    return [
        TextSuggestion(title=fav.name, text=str(resolve(fav.raw_path)), subtitle=fav.raw_path)
        for fav in ranked
    ]


def record_selection(suggestion: TextSuggestion, settings: Settings) -> None:
    """Bump frecency for the favorite FCC reports as picked.

    title/subtitle round-trip name/raw_path unchanged, so the usage key
    (`Favorite.to_line()` = ``name|raw_path``) matches what CLI use writes.
    """
    UsageStore(settings.usage_path).record(
        Favorite(name=suggestion.title, raw_path=suggestion.subtitle)
    )


def main() -> int:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    if not palette_mode():
        log.error("this binary only runs palette-managed by FastCommandCenter (pass --palette)")
        return EXIT_USAGE
    palette = FastToolPalette(TOOL_ID)
    palette.add_text_provider(
        PROVIDER_ID,
        lambda query, _session_id: build_suggestions(query, settings),
        on_selected=lambda suggestion: record_selection(suggestion, settings),
    )
    log.info("palette host running (tool_id=%s, favorites=%s)", TOOL_ID, settings.favorites_path)
    while True:
        palette.poll()
        time.sleep(POLL_INTERVAL_S)
