"""Resolve raw favorite paths. Only ~ is expanded — placeholders pass through."""

from __future__ import annotations

import os
from pathlib import Path


def resolve(raw_path: str) -> Path:
    return Path(os.path.expanduser(raw_path))


def collapse_home(path: Path) -> str:
    """Replace user home prefix with '~' for portable storage."""
    home = Path.home()
    try:
        rel = path.relative_to(home)
    except ValueError:
        return str(path)
    if str(rel) == ".":
        return "~"
    return f"~{os.sep}{rel}"
