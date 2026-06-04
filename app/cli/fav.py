"""fav — filter favorites and emit chosen path for the shell wrapper to cd into."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, bootstrap
from app.constants import ENV_TARGET_FILE
from app.favorites.filter import match
from app.favorites.path_resolver import resolve
from app.ui.menu import auto_pick_or_prompt


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fav",
        description="Filter favorite directories and print the chosen path.",
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

    index = auto_pick_or_prompt(candidates, highlight_index=0)
    if index is None:
        log.info("no selection made")
        return EXIT_FAILURE

    chosen = candidates[index]
    usage.record(chosen)
    resolved = str(resolve(chosen.raw_path))
    sys.stderr.write(f"> {chosen.name} | {resolved}\n")
    sys.stderr.flush()
    target_file = os.getenv(ENV_TARGET_FILE)
    if target_file:
        Path(target_file).write_text(resolved, encoding="utf-8")
    else:
        print(resolved)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
