from types import SimpleNamespace

import pytest

import ofscraper.managers.postcollection as postcollection
import ofscraper.utils.settings as settings


def _post(post_id, date):
    return SimpleNamespace(id=post_id, date=date)


def test_post_cap_keeps_newest(monkeypatch):
    monkeypatch.setattr(
        settings, "get_settings", lambda: SimpleNamespace(max_post_count_real=2)
    )
    collection = postcollection.PostCollection()
    collection._posts_map = {
        1: _post(1, "2024-01-01 00:00:00"),
        2: _post(2, "2024-03-01 00:00:00"),
        3: _post(3, "2024-02-01 00:00:00"),
    }
    assert [post.id for post in collection.posts] == [2, 3]


def test_post_cap_zero_means_unlimited(monkeypatch):
    monkeypatch.setattr(
        settings, "get_settings", lambda: SimpleNamespace(max_post_count_real=0)
    )
    collection = postcollection.PostCollection()
    collection._posts_map = {index: _post(index, "2024-01-01 00:00:00") for index in range(5)}
    assert len(collection.posts) == 5
