from __future__ import annotations

from pathlib import Path

import pytest

from app.favorites.entry import Favorite
from app.favorites.usage import UsageStore, recency_weight

DAY = 86_400.0


def _fav(name: str = "A", path: str = "/a") -> Favorite:
    return Favorite(name=name, raw_path=path)


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / ".favoritedirs.usage"


def test_missing_file_scores_zero(store_path: Path) -> None:
    store = UsageStore(store_path, now=lambda: 1000.0)
    assert store.score(_fav(), now=1000.0) == 0.0


def test_recency_weight_buckets() -> None:
    assert recency_weight(0.0) == 4.0
    assert recency_weight(2 * DAY) == 2.0
    assert recency_weight(10 * DAY) == 1.0
    assert recency_weight(60 * DAY) == 0.5
    assert recency_weight(200 * DAY) == 0.3


def test_record_increments_and_persists(store_path: Path) -> None:
    store = UsageStore(store_path, now=lambda: 1000.0)
    store.record(_fav())
    store.record(_fav())
    reopened = UsageStore(store_path, now=lambda: 1000.0)
    # count 2, last_used == now → within-a-day weight 4.0
    assert reopened.score(_fav(), now=1000.0) == pytest.approx(8.0)
    assert store_path.exists()


def test_score_decays_with_age(store_path: Path) -> None:
    store = UsageStore(store_path, now=lambda: 0.0)
    store.record(_fav())
    assert store.score(_fav(), now=0.0) == pytest.approx(4.0)
    assert store.score(_fav(), now=200 * DAY) == pytest.approx(0.3)


def test_sort_orders_by_frecency_and_is_stable(store_path: Path) -> None:
    store = UsageStore(store_path, now=lambda: 1000.0)
    a, b, c = _fav("A", "/a"), _fav("B", "/b"), _fav("C", "/c")
    store.record(b)
    # b bubbles to front; unused a and c keep their original file order
    assert store.sort([a, b, c]) == [b, a, c]


def test_unused_entries_keep_file_order(store_path: Path) -> None:
    store = UsageStore(store_path, now=lambda: 0.0)
    a, b = _fav("A", "/a"), _fav("B", "/b")
    assert store.sort([a, b]) == [a, b]


def test_remove_drops_entry(store_path: Path) -> None:
    store = UsageStore(store_path, now=lambda: 0.0)
    store.record(_fav())
    store.remove(_fav())
    assert store.score(_fav(), now=0.0) == 0.0


def test_corrupt_file_is_ignored(store_path: Path) -> None:
    store_path.write_text("not json {", encoding="utf-8")
    store = UsageStore(store_path, now=lambda: 0.0)
    assert store.score(_fav(), now=0.0) == 0.0
