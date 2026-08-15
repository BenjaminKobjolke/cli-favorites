"""Substring filter over favorite name + raw path (case-insensitive). Multi-token = AND.

Each token must appear as a literal substring in the joined ``name\\traw_path``
haystack. Tab joiner prevents a token from straddling the name/path boundary.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from app.constants import SCOPE_BOTH, SCOPE_NAME, SCOPE_PATH
from app.favorites.entry import Favorite, SearchScope

_HAYSTACK_SEP = "\t"


def match(
    favorites: list[Favorite],
    tokens: Sequence[str] | str | None,
    scope: SearchScope = SearchScope.BOTH,
) -> list[Favorite]:
    """Return favorites whose joined name+path contains ALL tokens.

    ``tokens`` may be ``None``/empty (returns all), a single string (split on
    whitespace), or a sequence of strings. ``scope`` restricts which field(s)
    are searched (name only, path only, or both — the default).
    """
    needles = _normalize(tokens)
    if not needles:
        return list(favorites)
    return [fav for fav in favorites if _matches_all(_haystack(fav, scope), needles)]


def add_scope_argument(parser: argparse.ArgumentParser) -> None:
    """Register the shared ``--scope`` flag on a CLI's argument parser."""
    parser.add_argument(
        "--scope",
        choices=(SCOPE_NAME, SCOPE_PATH, SCOPE_BOTH),
        default=SCOPE_BOTH,
        help="Restrict the filter to the favorite name, its path, or both (default).",
    )


def scope_from_args(value: str) -> SearchScope:
    """Map the ``--scope`` flag's string value to a SearchScope."""
    return SearchScope(value)


def _haystack(fav: Favorite, scope: SearchScope) -> str:
    return _HAYSTACK_SEP.join(fav.searchable_fields(scope)).casefold()


def _normalize(tokens: Sequence[str] | str | None) -> list[str]:
    if tokens is None:
        return []
    parts = tokens.split() if isinstance(tokens, str) else [t for t in tokens if t]
    return [p.casefold() for p in parts if p.strip()]


def _matches_all(haystack_cf: str, needles_cf: list[str]) -> bool:
    return all(n in haystack_cf for n in needles_cf)
