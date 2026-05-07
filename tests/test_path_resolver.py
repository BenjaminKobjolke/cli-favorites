from __future__ import annotations

from pathlib import Path

from app.favorites.path_resolver import collapse_home, resolve


def test_resolve_expands_tilde() -> None:
    resolved = resolve("~")
    assert resolved == Path.home()


def test_resolve_passes_through_absolute() -> None:
    assert resolve("C:/foo/bar") == Path("C:/foo/bar")


def test_resolve_does_not_expand_unknown_placeholder() -> None:
    raw = "{{Sync}}/something"
    assert resolve(raw) == Path(raw)


def test_collapse_home_replaces_prefix() -> None:
    inside = Path.home() / "Downloads"
    collapsed = collapse_home(inside)
    assert collapsed.startswith("~")
    assert collapsed.endswith("Downloads")


def test_collapse_home_leaves_external_path() -> None:
    outside = Path("C:/some/where")
    assert collapse_home(outside) == "C:\\some\\where" or collapse_home(outside) == "C:/some/where"
