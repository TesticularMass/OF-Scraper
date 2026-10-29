from types import SimpleNamespace as NS

import arrow

import ofscraper.utils.settings as settings
from ofscraper.managers.postcollection import PostCollection


def test_text_download_respects_the_date_range(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(
        actions=["download"], text=True, timed_only=None, filter=[], neg_filter=[], mass_msg=None,
        mediatypes=["Videos", "Audios", "Images"], post_sort="date", post_desc=False,
        before=arrow.get("2026-01-01"), after=arrow.get("2025-01-01"),
    ))
    collection = PostCollection(model_id=1, username="model")
    collection.add_posts([
        {"id": 1, "text": "inside the range", "postedAt": "2025-06-01"},
        {"id": 2, "text": "after the range", "postedAt": "2026-10-01"},
    ], actions=["text"])
    assert [post.id for post in collection.get_posts_for_text_download()] == [1]
