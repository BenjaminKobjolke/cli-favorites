"""Filesystem helpers. Atomic writes via temp file + os.replace."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, body: str) -> None:
    """Write ``body`` to ``path`` atomically.

    Creates parent directories, writes to a temp file in the same directory,
    then ``os.replace`` (atomic on POSIX and Windows). Cleans up the temp file
    on failure so a partial write never clobbers the target.
    """
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", dir=str(directory))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        os.replace(tmp_name, path)
    except OSError:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
