from __future__ import annotations

from pathlib import Path

import pytest

from app.favorites.entry import Favorite
from app.favorites.repository import FavoritesRepository


@pytest.fixture
def repo(tmp_path: Path) -> FavoritesRepository:
    return FavoritesRepository(tmp_path / ".favoritedirs")


def test_load_missing_file_returns_empty(repo: FavoritesRepository) -> None:
    assert repo.load() == []


def test_save_then_load_round_trip(repo: FavoritesRepository) -> None:
    items = [
        Favorite(name="Home", raw_path="~"),
        Favorite(name="Tmp", raw_path="C:/temp"),
    ]
    repo.save(items)
    assert repo.load() == items


def test_load_skips_blank_and_malformed_lines(repo: FavoritesRepository) -> None:
    repo.path.write_text(
        "Good|/a\n\n   \nbroken-line\nAnother|/b\n",
        encoding="utf-8",
    )
    favs = repo.load()
    assert [f.name for f in favs] == ["Good", "Another"]


def test_append_adds_one(repo: FavoritesRepository) -> None:
    repo.append(Favorite(name="A", raw_path="/a"))
    repo.append(Favorite(name="B", raw_path="/b"))
    assert [f.name for f in repo.load()] == ["A", "B"]


def test_remove_at_drops_entry(repo: FavoritesRepository) -> None:
    repo.save(
        [
            Favorite(name="A", raw_path="/a"),
            Favorite(name="B", raw_path="/b"),
            Favorite(name="C", raw_path="/c"),
        ]
    )
    removed = repo.remove_at(1)
    assert removed.name == "B"
    assert [f.name for f in repo.load()] == ["A", "C"]


def test_remove_at_out_of_range(repo: FavoritesRepository) -> None:
    with pytest.raises(IndexError):
        repo.remove_at(0)


def test_load_handles_cp1252_file(repo: FavoritesRepository) -> None:
    """User favorites files may be encoded in cp1252 (Windows legacy) rather than UTF-8."""
    content = "L\xfcddemann|D:/foo\nGood|/bar\n"
    repo.path.write_bytes(content.encode("cp1252"))
    favs = repo.load()
    assert [f.name for f in favs] == ["L\xfcddemann", "Good"]


def test_save_creates_parent_dir(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "dir" / ".favoritedirs"
    repo = FavoritesRepository(nested)
    repo.save([Favorite(name="A", raw_path="/a")])
    assert nested.read_text(encoding="utf-8") == "A|/a\n"
