"""Numbered-menu UI. All output goes to stderr to keep stdout clean for path capture."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

from app.favorites.entry import Favorite
from app.favorites.path_resolver import resolve
from app.ui.colors import dim, highlight, should_color


@dataclass(frozen=True)
class MenuStyle:
    """How the menu renders: which row to highlight, and color on/off/auto."""

    highlight_index: int | None = None
    color: bool | None = None


_DEFAULT_STYLE = MenuStyle()


def print_menu(
    items: list[Favorite],
    stream: TextIO | None = None,
    style: MenuStyle = _DEFAULT_STYLE,
) -> None:
    out = stream if stream is not None else sys.stderr
    use_color = should_color(out) if style.color is None else style.color
    for idx, fav in enumerate(items, start=1):
        resolved = resolve(fav.raw_path)
        line = f"{idx}. {fav.name} | {resolved}"
        if idx - 1 == style.highlight_index:
            line = highlight(line, use_color)
        else:
            line = dim(f"{idx}.", use_color) + line[len(f"{idx}.") :]
        out.write(f"{line}\n")
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
    style: MenuStyle = _DEFAULT_STYLE,
) -> int | None:
    """Auto-pick if exactly one item; otherwise show menu and prompt."""
    if not items:
        return None
    if len(items) == 1:
        return 0
    print_menu(items, out_stream, style)
    return prompt_index(len(items), in_stream, out_stream)
