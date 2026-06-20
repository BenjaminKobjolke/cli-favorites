"""Integration tests — spawn the CLI as a subprocess against an isolated favorites file."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env(favorites_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FAV_FILE"] = str(favorites_path)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["FAV_LOG_LEVEL"] = "WARNING"
    return env


def _run(
    module: str,
    args: list[str],
    favorites_path: Path,
    stdin: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=_env(favorites_path),
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )


@pytest.fixture
def fav_file(tmp_path: Path) -> Path:
    f = tmp_path / ".favoritedirs"
    f.write_text(
        "fman Data|~/AppData/Roaming/fman\nDownloads|~/Downloads\nProj|C:/work\n",
        encoding="utf-8",
    )
    return f


def test_fav_single_match_auto_picks(fav_file: Path) -> None:
    result = _run("app.cli.fav", ["fman"], fav_file)
    assert result.returncode == 0, result.stderr
    expected = str(Path(os.path.expanduser("~/AppData/Roaming/fman")))
    assert result.stdout.strip() == expected


def test_fav_no_match_exits_failure(fav_file: Path) -> None:
    result = _run("app.cli.fav", ["nothingmatches"], fav_file)
    assert result.returncode != 0
    assert result.stdout.strip() == ""


def test_fav_writes_to_target_file(fav_file: Path, tmp_path: Path) -> None:
    target_file = tmp_path / "target.txt"
    env = _env(fav_file)
    env["FAV_TARGET_FILE"] = str(target_file)
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.fav", "fman"],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    expected = str(Path(os.path.expanduser("~/AppData/Roaming/fman")))
    assert target_file.read_text(encoding="utf-8") == expected
    assert result.stdout.strip() == ""
    assert "fman Data" in result.stderr
    assert expected in result.stderr


def test_fav_no_match_does_not_create_target_file(fav_file: Path, tmp_path: Path) -> None:
    target_file = tmp_path / "target.txt"
    env = _env(fav_file)
    env["FAV_TARGET_FILE"] = str(target_file)
    result = subprocess.run(
        [sys.executable, "-m", "app.cli.fav", "nothingmatches"],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=15,
        check=False,
    )
    assert result.returncode != 0
    assert not target_file.exists()


def test_fav_multi_match_uses_input(fav_file: Path) -> None:
    fav_file.write_text(
        "fman Data|~/AppData/Roaming/fman\nFMAN User|~/.fman\n",
        encoding="utf-8",
    )
    result = _run("app.cli.fav", ["fman"], fav_file, stdin="2\n")
    assert result.returncode == 0, result.stderr
    expected = str(Path(os.path.expanduser("~/.fman")))
    assert result.stdout.strip() == expected


def test_fav_multi_match_empty_input_picks_top(fav_file: Path) -> None:
    fav_file.write_text(
        "fman Data|~/AppData/Roaming/fman\nFMAN User|~/.fman\n",
        encoding="utf-8",
    )
    # Bare Enter on the numbered fallback now accepts the highlighted top row.
    result = _run("app.cli.fav", ["fman"], fav_file, stdin="\n")
    assert result.returncode == 0, result.stderr
    expected = str(Path(os.path.expanduser("~/AppData/Roaming/fman")))
    assert result.stdout.strip() == expected


def test_fav_multi_match_invalid_input_fails(fav_file: Path) -> None:
    fav_file.write_text(
        "fman Data|~/AppData/Roaming/fman\nFMAN User|~/.fman\n",
        encoding="utf-8",
    )
    result = _run("app.cli.fav", ["fman"], fav_file, stdin="not a number\n")
    assert result.returncode != 0
    assert result.stdout.strip() == ""


def test_fav_add_with_name_flag(tmp_path: Path) -> None:
    fav_file = tmp_path / ".favoritedirs"
    fav_file.write_text("Existing|/x\n", encoding="utf-8")
    result = _run("app.cli.fav_add", ["--name", "MyDir"], fav_file)
    assert result.returncode == 0, result.stderr
    text = fav_file.read_text(encoding="utf-8")
    assert "Existing|/x" in text
    assert "MyDir|" in text


def test_fav_add_rejects_pipe_in_name(tmp_path: Path) -> None:
    fav_file = tmp_path / ".favoritedirs"
    fav_file.write_text("", encoding="utf-8")
    result = _run("app.cli.fav_add", ["--name", "bad|name"], fav_file)
    assert result.returncode != 0


def test_fav_del_removes_entry(fav_file: Path) -> None:
    result = _run("app.cli.fav_del", ["Downloads"], fav_file)
    assert result.returncode == 0, result.stderr
    text = fav_file.read_text(encoding="utf-8")
    assert "Downloads" not in text
    assert "fman Data" in text
    assert "Proj" in text


def test_fav_del_no_match_exits_failure(fav_file: Path) -> None:
    result = _run("app.cli.fav_del", ["nothingmatches"], fav_file)
    assert result.returncode != 0
    text = fav_file.read_text(encoding="utf-8")
    assert "fman Data" in text
    assert "Downloads" in text


def test_fav_frecency_promotes_picked_entry(fav_file: Path) -> None:
    fav_file.write_text(
        "fman Data|~/AppData/Roaming/fman\nFMAN User|~/.fman\n",
        encoding="utf-8",
    )
    usage_file = fav_file.with_name(fav_file.name + ".usage")

    # First run: file order is [fman Data, FMAN User]; pick #2 (FMAN User).
    first = _run("app.cli.fav", ["fman"], fav_file, stdin="2\n")
    assert first.returncode == 0, first.stderr
    assert first.stdout.strip() == str(Path(os.path.expanduser("~/.fman")))
    assert usage_file.exists()

    # Second run: FMAN User is now most-frecent, so #1 resolves to it.
    second = _run("app.cli.fav", ["fman"], fav_file, stdin="1\n")
    assert second.returncode == 0, second.stderr
    assert second.stdout.strip() == str(Path(os.path.expanduser("~/.fman")))


def test_fav_del_prunes_usage(fav_file: Path) -> None:
    fav_file.write_text(
        "fman Data|~/AppData/Roaming/fman\nFMAN User|~/.fman\n",
        encoding="utf-8",
    )
    usage_file = fav_file.with_name(fav_file.name + ".usage")

    picked = _run("app.cli.fav", ["fman"], fav_file, stdin="2\n")
    assert picked.returncode == 0, picked.stderr
    assert "FMAN User|~/.fman" in usage_file.read_text(encoding="utf-8")

    # FMAN User is now most-frecent → sorts to position #1 in the delete menu.
    removed = _run("app.cli.fav_del", ["fman"], fav_file, stdin="1\n")
    assert removed.returncode == 0, removed.stderr
    assert "FMAN User|~/.fman" not in usage_file.read_text(encoding="utf-8")
