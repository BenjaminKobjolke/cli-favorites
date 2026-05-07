from __future__ import annotations

import pytest

from app.favorites.entry import Favorite, InvalidFavoriteError, validate_name


def test_to_line_round_trip() -> None:
    fav = Favorite(name="fman Data", raw_path="~/AppData/Roaming/fman")
    parsed = Favorite.from_line(fav.to_line())
    assert parsed == fav


def test_from_line_strips_whitespace_around_pipe() -> None:
    fav = Favorite.from_line("FMAN User Home |~/.fman\n")
    assert fav.name == "FMAN User Home"
    assert fav.raw_path == "~/.fman"


def test_from_line_rejects_missing_pipe() -> None:
    with pytest.raises(InvalidFavoriteError):
        Favorite.from_line("no pipe here")


def test_from_line_rejects_empty_components() -> None:
    with pytest.raises(InvalidFavoriteError):
        Favorite.from_line("|/tmp")
    with pytest.raises(InvalidFavoriteError):
        Favorite.from_line("name|")


def test_from_line_keeps_path_with_pipe_in_value() -> None:
    """Only first '|' is the separator — path may contain another '|' (unlikely but safe)."""
    fav = Favorite.from_line("name|C:/weird|path")
    assert fav.name == "name"
    assert fav.raw_path == "C:/weird|path"


def test_validate_name_strips_and_returns() -> None:
    assert validate_name("  hello  ") == "hello"


def test_validate_name_rejects_empty() -> None:
    with pytest.raises(InvalidFavoriteError):
        validate_name("   ")


def test_validate_name_rejects_pipe() -> None:
    with pytest.raises(InvalidFavoriteError):
        validate_name("bad|name")


def test_validate_name_rejects_newline() -> None:
    with pytest.raises(InvalidFavoriteError):
        validate_name("multi\nline")
