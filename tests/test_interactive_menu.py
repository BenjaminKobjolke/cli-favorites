from __future__ import annotations

import io
from collections.abc import Callable

from app.favorites.entry import Favorite
from app.ui.interactive_menu import Key, KeyPress, select_interactive


def _favs(n: int) -> list[Favorite]:
    return [Favorite(name=f"Item{i}", raw_path=f"/p{i}") for i in range(n)]


def _reader(keys: list[KeyPress]) -> Callable[[], KeyPress]:
    it = iter(keys)

    def read() -> KeyPress:
        return next(it)

    return read


UP = KeyPress(Key.UP)
DOWN = KeyPress(Key.DOWN)
ENTER = KeyPress(Key.ENTER)
CANCEL = KeyPress(Key.CANCEL)


def _digit(c: str) -> KeyPress:
    return KeyPress(Key.CHAR, c)


def test_down_down_enter_selects_third() -> None:
    out = io.StringIO()
    keys = _reader([DOWN, DOWN, ENTER])
    assert select_interactive(_favs(5), read_key=keys, out_stream=out, color=False) == 2


def test_up_past_top_clamps_to_zero() -> None:
    out = io.StringIO()
    keys = _reader([UP, UP, ENTER])
    assert select_interactive(_favs(5), read_key=keys, out_stream=out, color=False) == 0


def test_enter_immediately_picks_highlighted_default() -> None:
    out = io.StringIO()
    keys = _reader([ENTER])
    assert (
        select_interactive(
            _favs(5), highlight_index=2, read_key=keys, out_stream=out, color=False
        )
        == 2
    )


def test_cancel_returns_none() -> None:
    out = io.StringIO()
    keys = _reader([DOWN, CANCEL])
    assert select_interactive(_favs(5), read_key=keys, out_stream=out, color=False) is None


def test_digit_selects_immediately() -> None:
    out = io.StringIO()
    keys = _reader([_digit("2")])  # 5 items: "2" cannot extend, picks at once
    assert select_interactive(_favs(5), read_key=keys, out_stream=out, color=False) == 1


def test_digit_then_enter_selects_that_row() -> None:
    out = io.StringIO()
    keys = _reader([_digit("3"), ENTER])
    assert select_interactive(_favs(5), read_key=keys, out_stream=out, color=False) == 2


def test_out_of_range_digit_ignored() -> None:
    out = io.StringIO()
    keys = _reader([_digit("9"), ENTER])
    assert select_interactive(_favs(5), read_key=keys, out_stream=out, color=False) == 0


def test_multi_digit_buffer() -> None:
    out = io.StringIO()
    keys = _reader([_digit("1"), _digit("2"), ENTER])
    assert select_interactive(_favs(12), read_key=keys, out_stream=out, color=False) == 11


def test_empty_list_returns_none() -> None:
    out = io.StringIO()
    keys = _reader([ENTER])
    assert select_interactive(_favs(0), read_key=keys, out_stream=out, color=False) is None


def test_renders_rows_to_stream() -> None:
    out = io.StringIO()
    keys = _reader([ENTER])
    select_interactive(_favs(3), read_key=keys, out_stream=out, color=False)
    text = out.getvalue()
    assert "1. Item0" in text
    assert "3. Item2" in text
