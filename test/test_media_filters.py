from types import SimpleNamespace as NS

import ofscraper.filters.media.filters as filters
import ofscraper.utils.settings as settings
from ofscraper.classes.of.posts import Post
from ofscraper.managers.postcollection import PostCollection


def test_mass_skip_keeps_posts_that_are_not_mass_messages(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(mass_msg=False))
    # Only messages carry isFromQueue; timeline posts leave it out.
    timeline = Post({"id": 1, "responseType": "post"}, 1, "model")
    direct = Post({"id": 2, "responseType": "message", "isFromQueue": False}, 1, "model")
    mass = Post({"id": 3, "responseType": "message", "isFromQueue": True}, 1, "model")
    assert filters.mass_msg_filter([timeline, direct, mass]) == [timeline, direct]


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
