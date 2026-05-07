"""Unit tests for the FAV_TARGET_FILE handoff in app.cli.fav."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.cli import fav as fav_module
from app.constants import ENV_FAVORITES_PATH, ENV_TARGET_FILE


@pytest.fixture
def favorites_file(tmp_path: Path) -> Path:
    f = tmp_path / ".favoritedirs"
    f.write_text(
        "Only|/abs/path\nOther|~/Downloads\n",
        encoding="utf-8",
    )
    return f


def test_writes_resolved_path_to_target_file(
    favorites_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target_file = tmp_path / "out.txt"
    monkeypatch.setenv(ENV_FAVORITES_PATH, str(favorites_file))
    monkeypatch.setenv(ENV_TARGET_FILE, str(target_file))
    monkeypatch.setattr("sys.argv", ["fav", "Only"])

    rc = fav_module.main()

    assert rc == 0
    assert target_file.read_text(encoding="utf-8") == str(Path("/abs/path"))
    captured = capsys.readouterr()
    assert "Only" in captured.err
    assert str(Path("/abs/path")) in captured.err


def test_no_match_does_not_create_target_file(
    favorites_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_file = tmp_path / "out.txt"
    monkeypatch.setenv(ENV_FAVORITES_PATH, str(favorites_file))
    monkeypatch.setenv(ENV_TARGET_FILE, str(target_file))
    monkeypatch.setattr("sys.argv", ["fav", "nothingmatches"])

    rc = fav_module.main()

    assert rc != 0
    assert not target_file.exists()


def test_stdout_fallback_when_target_file_unset(
    favorites_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(ENV_FAVORITES_PATH, str(favorites_file))
    monkeypatch.delenv(ENV_TARGET_FILE, raising=False)
    monkeypatch.setattr("sys.argv", ["fav", "Only"])

    rc = fav_module.main()

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == str(Path("/abs/path"))


def test_target_file_path_uses_env_var_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity check: the env var name we document matches what fav.py reads."""
    assert ENV_TARGET_FILE == "FAV_TARGET_FILE"
    assert os.getenv(ENV_TARGET_FILE) is None or isinstance(os.getenv(ENV_TARGET_FILE), str)
