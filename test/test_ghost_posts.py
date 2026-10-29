import asyncio

import pytest

import ofscraper.db.operations_.wrapper as wrapper
from ofscraper.classes.of.posts import Post
from ofscraper.db.operations_ import posts as posts_db


def _post(post_id, **flags):
    return Post({"id": post_id, "postedAt": "2026-01-01T00:00:00+00:00", "text": "", **flags}, 5, "model")


async def _filing(db):
    def ids(rows):
        return {row["post_id"] for row in rows}

    return (
        ids(await posts_db.get_timeline_posts_info(model_id=5, db_path=db)),
        ids(await posts_db.get_archived_post_info(model_id=5, db_path=db)),
        await posts_db.get_deleted_post_ids(model_id=5, db_path=db),
    )


# (post as stored, the scan it vanished from, the post as another scan found it,
#  expected (timeline cache, archived cache, deleted))
MOVES = [
    pytest.param({}, "Timeline", {"isArchived": True}, (set(), {1}, set()), id="archived"),
    pytest.param({}, "Timeline", {"isPinned": True}, (set(), set(), set()), id="pinned"),
    pytest.param({"isArchived": True}, "Archived", {}, ({1}, set(), set()), id="unarchived"),
]


@pytest.mark.parametrize("missing_first", [True, False])
@pytest.mark.parametrize("stored, vanished_from, found, expected", MOVES)
def test_a_moved_post_is_refiled_not_deleted(tmp_path, stored, vanished_from, found, expected, missing_first):
    db = tmp_path / "user_data.db"

    async def scan():
        await posts_db.create_post_table(db_path=db)
        await posts_db.write_post_table([_post(1, **stored)], model_id=5, db_path=db)
        # Areas are scanned concurrently, so either scan's write can land first.
        missing = posts_db.mark_post_as_deleted(post_ids=[1], model_id=5, area=vanished_from, db_path=db)
        found_again = posts_db.refresh_post_flags([_post(1, **found)], model_id=5, db_path=db)
        for write in (missing, found_again) if missing_first else (found_again, missing):
            await write
        return await _filing(db)

    assert asyncio.run(scan()) == expected


def test_a_post_no_scan_finds_is_flagged_deleted(tmp_path):
    db = tmp_path / "user_data.db"

    async def scan():
        await posts_db.create_post_table(db_path=db)
        await posts_db.write_post_table([_post(1)], model_id=5, db_path=db)
        await posts_db.mark_post_as_deleted(post_ids=[1], model_id=5, area="Timeline", db_path=db)
        return await _filing(db)

    assert asyncio.run(scan()) == (set(), set(), {1})


def test_a_scan_refiles_a_post_another_area_saved_first(monkeypatch, tmp_path):
    db = tmp_path / "user_data.db"
    monkeypatch.setattr(wrapper.placeholder, "databasePlaceholder",
                        lambda: type("Paths", (), {"databasePathHelper": lambda self, *args: db})())

    async def scan():
        await posts_db.create_post_table(db_path=db)
        # Purchased and Archived both see the post as new; the purchase data,
        # without the archive flag, is inserted first.
        await asyncio.gather(
            posts_db.make_post_table_changes([_post(1)], model_id=5, username="model"),
            posts_db.make_post_table_changes(
                [_post(1, isArchived=True)], model_id=5, username="model", refresh_flags=True
            ),
        )
        return await _filing(db)

    assert asyncio.run(scan()) == (set(), {1}, set())
