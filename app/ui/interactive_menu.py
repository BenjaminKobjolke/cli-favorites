"""Arrow-key interactive menu.

Renders a numbered list to stderr and lets the user move a cursor with Up/Down,
confirm with Enter (or by typing a number), and cancel with Esc/``q``. Key
reading is injected via ``read_key`` so the loop is testable without a real
console; the default reader uses ``msvcrt`` (Windows only). Callers should fall
back to the plain numbered prompt when no interactive reader is available.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TextIO

from app.favorites.entry import Favorite
from app.favorites.path_resolver import resolve
from app.ui.colors import dim, highlight, init_color, should_color

# ANSI redraw. We can't count lines to move the cursor up: long paths wrap to
# several physical terminal rows, so N menu entries != N screen lines. Instead we
# save the cursor at the menu's start, then on every redraw restore to it and
# clear everything below before reprinting. Each row also gets a leading CR
# because the Windows console treats LF as line-feed only (no carriage return).
_SAVE_CURSOR = "\x1b[s"
_RESTORE_CURSOR = "\x1b[u"
_CLEAR_TO_END = "\x1b[0J"
_CR = "\r"


class Key(Enum):
    """Logical key the menu loop reacts to."""

    UP = "up"
    DOWN = "down"
    ENTER = "enter"
    CANCEL = "cancel"
    CHAR = "char"
    OTHER = "other"


@dataclass(frozen=True)
class KeyPress:
    """A decoded key event. ``char`` carries the literal character for ``CHAR``."""

    kind: Key
    char: str = ""


def read_key_msvcrt() -> KeyPress:
    """Read one key from the Windows console and decode it into a KeyPress."""
    import msvcrt

    ch = msvcrt.getch()
    if ch in (b"\x00", b"\xe0"):  # special keys send a two-byte sequence
        code = msvcrt.getch()
        if code == b"H":
            return KeyPress(Key.UP)
        if code == b"P":
            return KeyPress(Key.DOWN)
        return KeyPress(Key.OTHER)
    if ch in (b"\r", b"\n"):
        return KeyPress(Key.ENTER)
    if ch in (b"\x1b", b"\x03"):  # Esc or Ctrl-C
        return KeyPress(Key.CANCEL)
    try:
        char = ch.decode("utf-8")
    except UnicodeDecodeError:
        return KeyPress(Key.OTHER)
    if char in ("q", "Q"):
        return KeyPress(Key.CANCEL)
    return KeyPress(Key.CHAR, char)


def reader_available() -> bool:
    """True when the default (msvcrt) key reader can be imported on this platform."""
    try:
        import msvcrt  # noqa: F401
    except ImportError:
        return False
    return True


def render_row(idx: int, fav: Favorite, is_highlight: bool, use_color: bool) -> str:
    """Format one menu row: ``N. name | resolved``, highlighted or with a dim number."""
    resolved = resolve(fav.raw_path)
    line = f"{idx}. {fav.name} | {resolved}"
    if is_highlight:
        return highlight(line, use_color)
    return dim(f"{idx}.", use_color) + line[len(f"{idx}.") :]


def _write_rows(items: list[Favorite], cursor: int, use_color: bool, out: TextIO) -> None:
    for idx, fav in enumerate(items, start=1):
        out.write(_CR + render_row(idx, fav, idx - 1 == cursor, use_color) + "\n")
    out.flush()


def _finish(out: TextIO, result: int | None) -> int | None:
    """Reset the cursor to column 0 so the caller's next line isn't indented."""
    out.write(_CR)
    out.flush()
    return result


def _draw(items: list[Favorite], cursor: int, use_color: bool, out: TextIO) -> None:
    out.write(_SAVE_CURSOR)
    _write_rows(items, cursor, use_color, out)


def _redraw(items: list[Favorite], cursor: int, use_color: bool, out: TextIO) -> None:
    out.write(_RESTORE_CURSOR + _CLEAR_TO_END)
    _write_rows(items, cursor, use_color, out)


def select_interactive(
    items: list[Favorite],
    *,
    highlight_index: int | None = 0,
    color: bool | None = None,
    read_key: Callable[[], KeyPress] | None = None,
    out_stream: TextIO | None = None,
) -> int | None:
    """Show an arrow-navigable menu; return the chosen 0-based index or None."""
    if not items:
        return None
    out = out_stream if out_stream is not None else sys.stderr
    reader = read_key if read_key is not None else read_key_msvcrt
    use_color = should_color(out) if color is None else color
    if use_color:
        init_color()

    cursor = min(max(highlight_index or 0, 0), len(items) - 1)
    buffer = ""
    _draw(items, cursor, use_color, out)

    while True:
        key = reader()
        if key.kind is Key.CANCEL:
            return _finish(out, None)
        if key.kind is Key.ENTER:
            return _finish(out, cursor)
        if key.kind is Key.UP:
            cursor = max(0, cursor - 1)
            buffer = ""
        elif key.kind is Key.DOWN:
            cursor = min(len(items) - 1, cursor + 1)
            buffer = ""
        elif key.kind is Key.CHAR and key.char.isdigit():
            value = int(buffer + key.char) if buffer else int(key.char)
            if not 1 <= value <= len(items):
                value = int(key.char)  # overflow: restart from this digit
            if not 1 <= value <= len(items):
                continue  # digit too large for the list: ignore
            buffer = str(value)
            cursor = value - 1
            if value * 10 > len(items):  # no larger index can extend it → pick now
                return _finish(out, cursor)
        else:
            continue  # unknown key: ignore, no redraw
        _redraw(items, cursor, use_color, out)
