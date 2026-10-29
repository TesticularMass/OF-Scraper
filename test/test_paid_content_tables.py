import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import ofscraper.data.posts.post as post_module
import ofscraper.utils.settings as settings


def test_purchased_messages_are_saved_as_messages(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(system_free_min=0))
    monkeypatch.setattr(post_module.paid, "get_paid_posts", AsyncMock(return_value=[
        {"id": 1, "responseType": "post"},
        {"id": 2, "responseType": "message"},
    ]))
    saved_posts, saved_messages = AsyncMock(), AsyncMock()
    monkeypatch.setattr(post_module.operations, "make_post_table_changes", saved_posts)
    monkeypatch.setattr(post_module.operations, "make_messages_table_changes", saved_messages)

    content, area = asyncio.run(post_module.process_paid_post(5, "model", None))

    assert [post.id for post in content] == [1, 2]
    # a message filed with the posts made the timeline scan flag it as deleted
    assert [post.id for post in saved_posts.call_args.args[0]] == [1]
    assert [post.id for post in saved_messages.call_args.args[0]] == [2]
