"""Centralized logging configuration. Logs go to stderr to keep stdout clean."""

from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(levelname)s %(name)s: %(message)s"


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format=LOG_FORMAT,
        stream=sys.stderr,
        force=True,
    )
