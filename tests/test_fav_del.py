"""Unit tests for fav-del's current-directory detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli.fav_del import _find_current
from app.favorites.entry import Favorite


def test_find_current_matches_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    favorites = [
        Favorite(name="Other", raw_path="C:/elsewhere"),
        Favorite(name="Here", raw_path=str(tmp_path)),
    ]
    found = _find_current(favorites)
    assert found is not None
    assert found.name == "Here"


def test_find_current_no_match_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    favorites = [Favorite(name="Other", raw_path="C:/elsewhere")]
    assert _find_current(favorites) is None


def test_find_current_empty_list_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert _find_current([]) is None


def test_find_current_is_case_insensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    favorites = [Favorite(name="Here", raw_path=str(tmp_path).upper())]
    found = _find_current(favorites)
    assert found is not None
    assert found.name == "Here"


def test_find_current_skips_unresolvable_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    favorites = [Favorite(name="Bad", raw_path="\0invalid")]
    assert _find_current(favorites) is None
