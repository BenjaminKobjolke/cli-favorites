from __future__ import annotations

import io

from app.favorites.entry import Favorite
from app.ui.menu import auto_pick_or_prompt, print_menu, prompt_index


def _favs(n: int) -> list[Favorite]:
    return [Favorite(name=f"Item{i}", raw_path=f"/p{i}") for i in range(n)]


def test_print_menu_writes_numbered_lines() -> None:
    out = io.StringIO()
    print_menu(_favs(2), stream=out)
    text = out.getvalue()
    assert "1. Item0" in text
    assert "2. Item1" in text


def test_prompt_index_valid() -> None:
    in_s = io.StringIO("2\n")
    out = io.StringIO()
    assert prompt_index(3, in_stream=in_s, out_stream=out) == 1


def test_prompt_index_out_of_range() -> None:
    in_s = io.StringIO("9\n")
    out = io.StringIO()
    assert prompt_index(3, in_stream=in_s, out_stream=out) is None


def test_prompt_index_non_numeric() -> None:
    in_s = io.StringIO("abc\n")
    out = io.StringIO()
    assert prompt_index(3, in_stream=in_s, out_stream=out) is None


def test_prompt_index_empty_line_returns_none() -> None:
    in_s = io.StringIO("\n")
    out = io.StringIO()
    assert prompt_index(3, in_stream=in_s, out_stream=out) is None


def test_auto_pick_single_item() -> None:
    in_s = io.StringIO("")
    out = io.StringIO()
    assert auto_pick_or_prompt(_favs(1), in_stream=in_s, out_stream=out) == 0


def test_auto_pick_empty_list() -> None:
    in_s = io.StringIO("")
    out = io.StringIO()
    assert auto_pick_or_prompt(_favs(0), in_stream=in_s, out_stream=out) is None


def test_auto_pick_multi_prompts() -> None:
    in_s = io.StringIO("3\n")
    out = io.StringIO()
    assert auto_pick_or_prompt(_favs(5), in_stream=in_s, out_stream=out) == 2
