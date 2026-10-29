import arrow
import pytest

import ofscraper.data.api.common.check as check


@pytest.fixture
def saved(monkeypatch):
    calls = []
    monkeypatch.setattr(check, "read_check_mode", lambda model_id, api: [{"id": 1}])
    monkeypatch.setattr(
        check,
        "set_check_mode_posts",
        lambda model_id, api, posts, update=False: calls.append(posts),
    )
    return calls


def test_a_full_scan_is_added_to_the_check_cache(saved):
    # get_after starts every full scan at 2000, never at 0
    check.update_check([{"id": 2}], 5, arrow.get("2000").float_timestamp, "Timeline")
    assert saved == [[{"id": 2}, {"id": 1}]]


def test_a_partial_scan_leaves_the_check_cache_alone(saved):
    check.update_check([{"id": 2}], 5, arrow.get("2024-01-01").float_timestamp, "Timeline")
    assert saved == []
