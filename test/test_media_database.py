import asyncio
import sqlite3
from contextlib import closing
from types import SimpleNamespace as NS

from ofscraper.db.merge import MergeDatabase
from ofscraper.db.operations_ import media as media_db


def media_record(post_id=8):
    return NS(
        id=7, post_id=post_id, link="https://example.invalid/file.jpg",
        responsetype="Timeline", mediatype="Images", preview=0, linked=True,
        date="2026-01-01", postdate="2026-01-01", duration_string=None, canview=True,
    )


def test_shared_database_keeps_each_models_media(tmp_path):
    db = tmp_path / "shared.db"

    async def insert():
        await media_db.create_media_table(db_path=db)
        await media_db.batch_mediainsert([media_record()], model_id=1, db_path=db)
        await media_db.batch_mediainsert([media_record()], model_id=2, db_path=db)

    asyncio.run(insert())
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT model_id FROM medias ORDER BY model_id").fetchall() == [(1,), (2,)]


def test_new_undownloaded_media_reach_stray_cleanup(tmp_path):
    db = tmp_path / "media.db"

    async def insert_and_query():
        await media_db.create_media_table(db_path=db)
        await media_db.batch_mediainsert([media_record()], model_id=1, db_path=db)
        return await media_db.get_unlocked_media_ids(model_id=1, db_path=db)

    assert asyncio.run(insert_and_query()) == [{"media_id": 7, "post_id": 8}]


def test_merge_keeps_media_shared_by_two_posts(tmp_path):
    destination, source = tmp_path / "dest.db", tmp_path / "source.db"

    async def merge():
        for db, post_id in ((destination, 8), (source, 99)):
            await media_db.create_media_table(db_path=db)
            await media_db.batch_mediainsert([media_record(post_id)], model_id=1, db_path=db)
        merger = MergeDatabase()
        merger._new_db = destination
        rows = await media_db.get_all_medias_transition(db_path=destination)
        merger._curr_medias = {tuple(row[key] for key in merger._media_keys) for row in rows}
        await merger.merge_media_helper(source)

    asyncio.run(merge())
    with closing(sqlite3.connect(destination)) as conn:
        assert conn.execute("SELECT post_id FROM medias ORDER BY post_id").fetchall() == [(8,), (99,)]
