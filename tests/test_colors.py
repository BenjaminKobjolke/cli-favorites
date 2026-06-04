from __future__ import annotations

import io

import pytest

from app.constants import ENV_COLOR, ENV_NO_COLOR
from app.ui.colors import dim, highlight, should_color


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def _clean_color_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_COLOR, raising=False)
    monkeypatch.delenv(ENV_NO_COLOR, raising=False)


def test_should_color_false_for_non_tty() -> None:
    assert should_color(io.StringIO()) is False


def test_should_color_true_for_tty() -> None:
    assert should_color(_Tty()) is True


def test_no_color_env_disables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_NO_COLOR, "1")
    assert should_color(_Tty()) is False


def test_fav_color_forces_on_even_for_non_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_NO_COLOR, "1")
    monkeypatch.setenv(ENV_COLOR, "always")
    assert should_color(io.StringIO()) is True


def test_fav_color_forces_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_COLOR, "0")
    assert should_color(_Tty()) is False


def test_highlight_wraps_when_enabled() -> None:
    out = highlight("x", True)
    assert out != "x"
    assert "x" in out
    assert "\x1b[" in out


def test_passthrough_when_disabled() -> None:
    assert highlight("x", False) == "x"
    assert dim("x", False) == "x"
