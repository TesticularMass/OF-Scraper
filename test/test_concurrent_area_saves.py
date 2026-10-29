import asyncio

import pytest

import ofscraper.db.operations_.wrapper as wrapper
from ofscraper.classes.of.posts import Post
from ofscraper.db.operations_ import messages as messages_db
from ofscraper.db.operations_ import posts as posts_db
from ofscraper.db.operations_ import stories as stories_db


# (create table, save the area's results, read the saved ids)
TABLES = [
    pytest.param(posts_db.create_post_table, posts_db.make_post_table_changes, posts_db.get_all_post_ids,
                 "Timeline", id="posts"),
    pytest.param(messages_db.create_message_table, messages_db.make_messages_table_changes,
                 messages_db.get_all_messages_ids, "Messages", id="messages"),
    pytest.param(stories_db.create_stories_table, stories_db.make_stories_table_changes,
                 stories_db.get_all_stories_ids, "Stories", id="stories"),
]


@pytest.mark.parametrize("create, save, saved_ids, area", TABLES)
def test_two_areas_can_save_the_same_new_item_at_once(monkeypatch, tmp_path, create, save, saved_ids, area):
    db = tmp_path / "user_data.db"
    monkeypatch.setattr(wrapper.placeholder, "databasePlaceholder",
                        lambda: type("Paths", (), {"databasePathHelper": lambda self, *args: db})())
    # e.g. a purchased timeline post, or a story that is also in a highlight
    item = Post({"id": 1, "postedAt": "2026-01-01T00:00:00+00:00", "text": ""}, 5, "model", area)

    async def scan():
        await create(model_id=5, username="model")
        await asyncio.gather(*(save([item], model_id=5, username="model") for _ in range(2)))
        return await saved_ids(model_id=5, username="model")

    assert asyncio.run(scan()) == [1]
