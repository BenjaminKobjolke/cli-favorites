"""fav-del — filter favorites and delete the chosen entry."""

from __future__ import annotations

import argparse
import sys

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, bootstrap
from app.favorites.filter import match
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
        help="Filter tokens (AND, case-insensitive substring). Empty = list all.",
    )
    return parser.parse_args(argv)


def main() -> int:
    _, repo, usage, log = bootstrap()
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE

    favorites = repo.load()
    if not favorites:
        log.error("no favorites found in %s", repo.path)
        return EXIT_FAILURE

    candidates = usage.sort(match(favorites, args.query))
    if not candidates:
        log.error("no favorites match %s", " ".join(args.query) or "<empty>")
        return EXIT_FAILURE

    index = auto_pick_or_prompt(candidates, style=MenuStyle(highlight_index=0))
    if index is None:
        log.info("no selection made")
        return EXIT_FAILURE

    chosen = candidates[index]
    real_index = favorites.index(chosen)
    try:
        removed = repo.remove_at(real_index)
    except (OSError, IndexError) as err:
        log.error("failed to delete entry: %s", err)
        return EXIT_FAILURE

    usage.remove(removed)
    log.info("deleted: %s | %s", removed.name, removed.raw_path)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
