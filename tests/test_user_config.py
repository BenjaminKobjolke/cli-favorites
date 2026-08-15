"""Tests for the persistent user config sidecar."""

from __future__ import annotations

import json
from pathlib import Path

from app.config.user_config import UserConfig
from app.constants import DEFAULT_MAX_RESULTS


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = UserConfig.load(tmp_path / ".favoritedirs.config")
    assert cfg.max_results == DEFAULT_MAX_RESULTS


def test_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / ".favoritedirs.config"
    UserConfig(max_results=25).save(path)
    assert UserConfig.load(path).max_results == 25


def test_load_corrupt_json_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / ".favoritedirs.config"
    path.write_text("{not json", encoding="utf-8")
    assert UserConfig.load(path).max_results == DEFAULT_MAX_RESULTS


def test_load_non_dict_returns_defaults(tmp_path: Path) -> None:
    path = tmp_path / ".favoritedirs.config"
    path.write_text("[1, 2]", encoding="utf-8")
    assert UserConfig.load(path).max_results == DEFAULT_MAX_RESULTS


def test_load_invalid_values_return_defaults(tmp_path: Path) -> None:
    path = tmp_path / ".favoritedirs.config"
    for bad in ["ten", 0, -3, 2.5, True, None]:
        path.write_text(json.dumps({"max_results": bad}), encoding="utf-8")
        assert UserConfig.load(path).max_results == DEFAULT_MAX_RESULTS
