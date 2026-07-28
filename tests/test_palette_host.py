"""Tests for the FastCommandCenter palette host's suggestion building."""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.config.settings import Settings
from app.palette_host import build_suggestions


def _settings(tmp_path: Path) -> Settings:
    favorites_path = tmp_path / ".favoritedirs"
    return Settings(
        favorites_path=favorites_path,
        usage_path=favorites_path.with_name(favorites_path.name + ".usage"),
        log_level="INFO",
    )


def _write_favorites(settings: Settings, lines: list[str]) -> None:
    settings.favorites_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_empty_query_returns_all(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_favorites(settings, ["proj|C:\\code\\proj", "docs|C:\\docs"])
    results = build_suggestions("", settings)
    assert [r.title for r in results] == ["proj", "docs"]


def test_query_filters_with_and_substrings(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_favorites(
        settings,
        [
            "erp api|D:\\wamp64\\www\\erp-api",
            "erp front|D:\\wamp64\\www\\erp-frontend",
            "notes|C:\\notes",
        ],
    )
    results = build_suggestions("erp front", settings)
    assert [r.title for r in results] == ["erp front"]


def test_frecency_orders_results(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_favorites(settings, ["cold|C:\\cold", "hot|C:\\hot"])
    usage = {"hot|C:\\hot": {"count": 5, "last_used": time.time()}}
    settings.usage_path.write_text(json.dumps(usage), encoding="utf-8")
    results = build_suggestions("", settings)
    assert [r.title for r in results] == ["hot", "cold"]


def test_text_is_resolved_path_and_subtitle_is_raw(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _write_favorites(settings, ["home notes|~\\notes"])
    results = build_suggestions("notes", settings)
    assert results[0].text == str(Path.home() / "notes")
    assert results[0].subtitle == "~\\notes"


def test_missing_favorites_file_returns_empty(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    assert build_suggestions("anything", settings) == []
