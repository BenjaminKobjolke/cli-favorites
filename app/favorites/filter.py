"""Substring filter over favorite name + raw path (case-insensitive). Multi-token = AND.

Each token must appear as a literal substring in the joined ``name\\traw_path``
haystack. Tab joiner prevents a token from straddling the name/path boundary.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.favorites.entry import Favorite

_HAYSTACK_SEP = "\t"


def match(favorites: list[Favorite], tokens: Sequence[str] | str | None) -> list[Favorite]:
    """Return favorites whose joined name+path contains ALL tokens.

    ``tokens`` may be ``None``/empty (returns all), a single string (split on
    whitespace), or a sequence of strings.
    """
    needles = _normalize(tokens)
    if not needles:
        return list(favorites)
    return [fav for fav in favorites if _matches_all(_haystack(fav), needles)]


def _haystack(fav: Favorite) -> str:
    return _HAYSTACK_SEP.join(fav.searchable_fields()).casefold()


def _normalize(tokens: Sequence[str] | str | None) -> list[str]:
    if tokens is None:
        return []
    parts = tokens.split() if isinstance(tokens, str) else [t for t in tokens if t]
    return [p.casefold() for p in parts if p.strip()]


def _matches_all(haystack_cf: str, needles_cf: list[str]) -> bool:
    return all(n in haystack_cf for n in needles_cf)
