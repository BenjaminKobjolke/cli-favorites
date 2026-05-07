"""Numbered-menu UI. All output goes to stderr to keep stdout clean for path capture."""

from __future__ import annotations

import sys
from typing import TextIO

from app.favorites.entry import Favorite
from app.favorites.path_resolver import resolve


def print_menu(items: list[Favorite], stream: TextIO | None = None) -> None:
    out = stream if stream is not None else sys.stderr
    for idx, fav in enumerate(items, start=1):
        resolved = resolve(fav.raw_path)
        out.write(f"{idx}. {fav.name} | {resolved}\n")
    out.flush()


def prompt_index(
    count: int,
    in_stream: TextIO | None = None,
    out_stream: TextIO | None = None,
) -> int | None:
    """Read a 1-based index from stdin. Return 0-based index, or None on cancel/invalid."""
    out = out_stream if out_stream is not None else sys.stderr
    src = in_stream if in_stream is not None else sys.stdin
    out.write(f"Select [1-{count}]: ")
    out.flush()
    try:
        line = src.readline()
    except (EOFError, KeyboardInterrupt):
        return None
    if not line:
        return None
    raw = line.strip()
    if not raw:
        return None
    try:
        choice = int(raw)
    except ValueError:
        return None
    if choice < 1 or choice > count:
        return None
    return choice - 1


def auto_pick_or_prompt(
    items: list[Favorite],
    in_stream: TextIO | None = None,
    out_stream: TextIO | None = None,
) -> int | None:
    """Auto-pick if exactly one item; otherwise show menu and prompt."""
    if not items:
        return None
    if len(items) == 1:
        return 0
    print_menu(items, out_stream)
    return prompt_index(len(items), in_stream, out_stream)
