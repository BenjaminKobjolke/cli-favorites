"""fav-del — filter favorites and delete the chosen entry."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, bootstrap
from app.config.user_config import UserConfig
from app.favorites.entry import Favorite
from app.favorites.filter import add_scope_argument, match, scope_from_args
from app.favorites.path_resolver import resolve
from app.favorites.repository import FavoritesRepository
from app.favorites.usage import UsageStore
from app.ui.menu import MenuStyle, auto_pick_or_prompt


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fav-del",
        description="Delete a favorite directory entry.",
    )
    parser.add_argument(
        "query",
        nargs="*",
        default=[],
        help="Filter tokens (AND, case-insensitive substring). Empty = current dir or list all.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts.",
    )
    add_scope_argument(parser)
    return parser.parse_args(argv)


def _find_current(favorites: list[Favorite]) -> Favorite | None:
    """Return the favorite whose resolved path matches the current directory, if any."""
    try:
        cwd = os.path.normcase(os.path.normpath(str(Path.cwd())))
    except (OSError, ValueError):
        return None
    for fav in favorites:
        try:
            candidate = os.path.normcase(os.path.normpath(str(resolve(fav.raw_path))))
        except (OSError, ValueError):
            continue
        if candidate == cwd:
            return fav
    return None


def _confirm(prompt: str, *, skip: bool) -> bool:
    if skip:
        return True
    sys.stderr.write(prompt)
    sys.stderr.flush()
    answer = sys.stdin.readline().strip().lower()
    return answer == "y"


def _remove(
    repo: FavoritesRepository,
    usage: UsageStore,
    favorites: list[Favorite],
    chosen: Favorite,
    log: logging.Logger,
) -> int:
    real_index = favorites.index(chosen)
    try:
        removed = repo.remove_at(real_index)
    except (OSError, IndexError) as err:
        log.error("failed to delete entry: %s", err)
        return EXIT_FAILURE
    usage.remove(removed)
    log.info("deleted: %s | %s", removed.name, removed.raw_path)
    return EXIT_OK


def main() -> int:
    settings, repo, usage, log = bootstrap()
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE

    favorites = repo.load()
    if not favorites:
        log.error("no favorites found in %s", repo.path)
        return EXIT_FAILURE

    if not args.query:
        current = _find_current(favorites)
        if current is not None:
            confirmed = _confirm(
                f"Current folder is a favorite: {current.name} | {current.raw_path}\n"
                "Delete favorite link? [y/N]: ",
                skip=args.yes,
            )
            if confirmed:
                return _remove(repo, usage, favorites, current, log)
            # declined — fall through to the normal picker below

    candidates = usage.sort(match(favorites, args.query, scope=scope_from_args(args.scope)))
    if not candidates:
        log.error("no favorites match %s", " ".join(args.query) or "<empty>")
        return EXIT_FAILURE
    candidates = candidates[: UserConfig.load(settings.config_path).max_results]

    index = auto_pick_or_prompt(candidates, style=MenuStyle(highlight_index=0))
    if index is None:
        log.info("no selection made")
        return EXIT_FAILURE

    chosen = candidates[index]
    if not _confirm(
        f"Delete favorite link: {chosen.name} | {chosen.raw_path}? [y/N]: ", skip=args.yes
    ):
        log.info("cancelled")
        return EXIT_FAILURE

    return _remove(repo, usage, favorites, chosen, log)


if __name__ == "__main__":
    sys.exit(main())
