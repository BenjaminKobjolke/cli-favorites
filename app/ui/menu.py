"""Numbered-menu UI. All output goes to stderr to keep stdout clean for path capture."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

from app.favorites.entry import Favorite
from app.ui.colors import should_color
from app.ui.interactive_menu import reader_available, render_row, select_interactive


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
        line = render_row(idx, fav, idx - 1 == style.highlight_index, use_color)
        out.write(f"{line}\n")
    out.flush()


def prompt_index(
    count: int,
    in_stream: TextIO | None = None,
    out_stream: TextIO | None = None,
    default_index: int | None = None,
) -> int | None:
    """Read a 1-based index from stdin. Return 0-based index, or None on cancel/invalid.

    An empty line returns ``default_index`` (e.g. the highlighted row) when given,
    otherwise None.
    """
    out = out_stream if out_stream is not None else sys.stderr
    src = in_stream if in_stream is not None else sys.stdin
    out.write(f"Select [1-{count}]: ")
    out.flush()
    try:
        line = src.readline()
    except (EOFError, KeyboardInterrupt):
        return None
    if not line:
        return default_index
    raw = line.strip()
    if not raw:
        return default_index
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
    """Auto-pick if exactly one item; otherwise show menu and prompt.

    Uses the arrow-key interactive menu on a real console; falls back to the
    numbered prompt when stderr is not a TTY (piped input, tests) or no
    interactive key reader is available.
    """
    if not items:
        return None
    if len(items) == 1:
        return 0
    out = out_stream if out_stream is not None else sys.stderr
    if _interactive_capable(out):
        return select_interactive(
            items,
            highlight_index=style.highlight_index,
            color=style.color,
            out_stream=out,
        )
    print_menu(items, out_stream, style)
    return prompt_index(len(items), in_stream, out_stream, default_index=style.highlight_index)


def _interactive_capable(out: TextIO) -> bool:
    isatty = getattr(out, "isatty", None)
    is_tty = bool(isatty()) if callable(isatty) else False
    return is_tty and reader_available()
