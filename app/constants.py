"""Centralized string and path constants for cli-favorites."""

from __future__ import annotations

FAVORITES_FILENAME = ".favoritedirs"
FIELD_SEPARATOR = "|"
USAGE_FILENAME_SUFFIX = ".usage"

ENV_FAVORITES_PATH = "FAV_FILE"
ENV_LOG_LEVEL = "FAV_LOG_LEVEL"
ENV_TARGET_FILE = "FAV_TARGET_FILE"
ENV_NO_COLOR = "NO_COLOR"
ENV_COLOR = "FAV_COLOR"

LOG_NAME = "cli_favorites"

_DAY_SECONDS = 86_400.0

# Frecency recency multipliers: (max_age_seconds, weight). First match wins;
# anything older than the last bound uses RECENCY_WEIGHT_DEFAULT.
RECENCY_WEIGHTS: tuple[tuple[float, float], ...] = (
    (1 * _DAY_SECONDS, 4.0),
    (7 * _DAY_SECONDS, 2.0),
    (30 * _DAY_SECONDS, 1.0),
    (90 * _DAY_SECONDS, 0.5),
)
RECENCY_WEIGHT_DEFAULT = 0.3
