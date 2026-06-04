"""fav-add — append the current directory as a new favorite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cli._common import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, bootstrap
from app.favorites.entry import Favorite, InvalidFavoriteError, validate_name
from app.favorites.path_resolver import collapse_home


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fav-add",
        description="Add the current directory as a favorite.",
    )
    parser.add_argument(
        "--name",
        help="Favorite name. If omitted, you will be prompted.",
    )
    return parser.parse_args(argv)


def _read_name_interactive() -> str:
    sys.stderr.write("Name: ")
    sys.stderr.flush()
    line = sys.stdin.readline()
    if not line:
        raise InvalidFavoriteError("no name provided")
    return line.strip()


def main() -> int:
    _, repo, _usage, log = bootstrap()
    try:
        args = _parse_args(sys.argv[1:])
    except SystemExit as err:
        return int(err.code) if isinstance(err.code, int) else EXIT_USAGE

    cwd = Path.cwd()
    raw_path = collapse_home(cwd)

    try:
        provided = args.name if args.name is not None else _read_name_interactive()
        name = validate_name(provided)
    except InvalidFavoriteError as err:
        log.error("invalid name: %s", err)
        return EXIT_FAILURE

    favorite = Favorite(name=name, raw_path=raw_path)
    try:
        repo.append(favorite)
    except OSError as err:
        log.error("failed to write %s: %s", repo.path, err)
        return EXIT_FAILURE

    log.info("added: %s | %s", favorite.name, favorite.raw_path)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
