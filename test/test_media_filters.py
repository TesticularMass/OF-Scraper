from types import SimpleNamespace as NS

import ofscraper.utils.settings as settings
from ofscraper.managers.postcollection import PostCollection


def test_text_posts_without_a_date_sort_first(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(
        actions=["download"], text=True, timed_only=None, filter=[], neg_filter=[], mass_msg=None,
        mediatypes=["Videos", "Audios", "Images"], post_sort="date", post_desc=False,
        before=None, after=None,
    ))
    collection = PostCollection(model_id=1, username="model")
    collection.add_posts([
        {"id": 1, "text": "a dated post", "postedAt": "2025-06-01"},
        # profile posts are dated by the join date, which restricted accounts hide
        {"id": 2, "text": "profile bio", "postedAt": None},
    ], actions=["text"])
    assert [post.id for post in collection.get_posts_for_text_download()] == [2, 1]
