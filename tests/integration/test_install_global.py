"""Integration tests for the install_global command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["FAV_LOG_LEVEL"] = "WARNING"
    return env


def test_install_writes_three_bats(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.install_global", str(tmp_path)],
        capture_output=True,
        text=True,
        env=_env(),
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "fav.bat").exists()
    assert (tmp_path / "fav-add.bat").exists()
    assert (tmp_path / "fav-del.bat").exists()


def test_install_capture_bat_uses_target_file(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, "-m", "app.cli.install_global", str(tmp_path)],
        capture_output=True,
        text=True,
        env=_env(),
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    fav_bat = (tmp_path / "fav.bat").read_text(encoding="utf-8")
    assert "FAV_TARGET_FILE" in fav_bat
    assert "cd /d" in fav_bat
    assert "for /f" not in fav_bat
    assert "app.cli.fav" in fav_bat
    assert 'set "PYTHONSAFEPATH=1"' in fav_bat


def test_install_plain_bat_no_cd(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, "-m", "app.cli.install_global", str(tmp_path)],
        capture_output=True,
        text=True,
        env=_env(),
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    add_bat = (tmp_path / "fav-add.bat").read_text(encoding="utf-8")
    assert "cd /d" not in add_bat
    assert "FAV_TARGET_FILE" not in add_bat
    assert "app.cli.fav_add" in add_bat
    assert 'set "PYTHONSAFEPATH=1"' in add_bat


def test_install_refuses_overwrite_without_force(tmp_path: Path) -> None:
    (tmp_path / "fav.bat").write_text("existing", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.install_global", str(tmp_path)],
        input="n\n",
        capture_output=True,
        text=True,
        env=_env(),
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    assert result.returncode != 0
    assert (tmp_path / "fav.bat").read_text(encoding="utf-8") == "existing"


def test_install_force_overwrites(tmp_path: Path) -> None:
    (tmp_path / "fav.bat").write_text("existing", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.install_global", str(tmp_path), "--force"],
        capture_output=True,
        text=True,
        env=_env(),
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "fav.bat").read_text(encoding="utf-8") != "existing"
