from __future__ import annotations

from app.favorites.entry import Favorite, SearchScope
from app.favorites.filter import match


def _favs() -> list[Favorite]:
    return [
        Favorite(name="fman Data", raw_path="~/AppData/fman"),
        Favorite(name="FMAN User Home", raw_path="~/.fman"),
        Favorite(name="Downloads", raw_path="~/Downloads"),
        Favorite(name="ERP API", raw_path="D:/erp-api"),
        Favorite(name="ERP Frontend", raw_path="D:/erp-frontend"),
    ]


def test_empty_query_returns_all() -> None:
    assert len(match(_favs(), "")) == 5
    assert len(match(_favs(), None)) == 5
    assert len(match(_favs(), [])) == 5


def test_single_token_case_insensitive() -> None:
    result = match(_favs(), "fman")
    assert [f.name for f in result] == ["fman Data", "FMAN User Home"]


def test_string_with_spaces_splits_into_tokens() -> None:
    result = match(_favs(), "erp api")
    assert [f.name for f in result] == ["ERP API"]


def test_token_list_ands_all_tokens() -> None:
    result = match(_favs(), ["erp", "api"])
    assert [f.name for f in result] == ["ERP API"]


def test_token_order_does_not_matter() -> None:
    a = match(_favs(), ["api", "erp"])
    b = match(_favs(), ["erp", "api"])
    assert a == b == [_favs()[3]]


def test_no_match_returns_empty() -> None:
    assert match(_favs(), "nothingmatches") == []
    assert match(_favs(), ["erp", "downloads"]) == []


def test_match_against_path() -> None:
    """Path tokens are searched too: 'AppData' lives only in path of 'fman Data'."""
    result = match(_favs(), "AppData")
    assert [f.name for f in result] == ["fman Data"]


def test_no_match_for_nonexistent_substring() -> None:
    """Token absent from name and path: no match."""
    result = match(_favs(), "zzqq")
    assert result == []


def test_token_with_tab_never_matches() -> None:
    """Joiner is a tab. A query token containing tab can't straddle name/path."""
    result = match(_favs(), ["fman\tDownloads"])
    assert result == []


def test_path_substring_with_dashes() -> None:
    """`erp-api` should match the entry whose path is 'D:/erp-api'."""
    result = match(_favs(), "erp-api")
    assert [f.name for f in result] == ["ERP API"]


def test_name_and_path_tokens_combined() -> None:
    """Tokens AND across the joined haystack: 'erp' (name) + 'api' (path)."""
    result = match(_favs(), ["erp", "api"])
    assert [f.name for f in result] == ["ERP API"]


def test_scope_name_excludes_path_only_match() -> None:
    """'AppData' lives only in the path of 'fman Data' — NAME scope must miss it."""
    result = match(_favs(), "AppData", scope=SearchScope.NAME)
    assert result == []


def test_scope_path_excludes_name_only_match() -> None:
    """A token only present in the name must miss under PATH scope."""
    favs = [Favorite(name="Unique Nickname", raw_path="D:/some/dir")]
    result = match(favs, "Nickname", scope=SearchScope.PATH)
    assert result == []


def test_scope_path_matches_path_substring() -> None:
    result = match(_favs(), "erp-api", scope=SearchScope.PATH)
    assert [f.name for f in result] == ["ERP API"]


def test_scope_name_matches_name_substring() -> None:
    result = match(_favs(), "fman", scope=SearchScope.NAME)
    assert [f.name for f in result] == ["fman Data", "FMAN User Home"]


def test_scope_default_is_both() -> None:
    assert match(_favs(), "AppData") == match(_favs(), "AppData", scope=SearchScope.BOTH)
