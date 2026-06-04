"""Terminal color helpers. No-ops when output is not an interactive terminal."""

from __future__ import annotations

import os
import sys
from typing import TextIO

import colorama
from colorama import Fore, Style

from app.constants import ENV_COLOR, ENV_NO_COLOR

_TRUTHY = {"1", "true", "yes", "always", "on"}


def init_color() -> None:
    """Enable ANSI handling on legacy Windows consoles. Safe to call repeatedly."""
    colorama.just_fix_windows_console()


def should_color(stream: TextIO | None = None) -> bool:
    """Decide whether to emit color.

    ``FAV_COLOR`` forces the answer (truthy = on, anything else = off). Else the
    standard ``NO_COLOR`` (present = off) wins. Otherwise color only when the
    stream is a real terminal.
    """
    out = stream if stream is not None else sys.stderr
    override = os.getenv(ENV_COLOR)
    if override is not None:
        return override.strip().lower() in _TRUTHY
    if os.getenv(ENV_NO_COLOR) is not None:
        return False
    isatty = getattr(out, "isatty", None)
    return bool(isatty()) if callable(isatty) else False


def highlight(text: str, enabled: bool = True) -> str:
    """Bright color — used for the top (most-frecent) result."""
    if not enabled:
        return text
    return f"{Style.BRIGHT}{Fore.GREEN}{text}{Style.RESET_ALL}"


def dim(text: str, enabled: bool = True) -> str:
    if not enabled:
        return text
    return f"{Style.DIM}{text}{Style.RESET_ALL}"
