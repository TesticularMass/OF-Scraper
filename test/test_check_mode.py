import asyncio
from types import SimpleNamespace as NS

import ofscraper.commands.check as check
import ofscraper.utils.settings as settings
from ofscraper.managers.postcollection import PostCollection
from ofscraper.utils.args.parse.commands.post import post_check


def collection_for(model_id, media_ids):
    collection = PostCollection(model_id=model_id, username=f"model{model_id}")
    collection.add_posts([
        {
            "id": model_id * 100 + media_id, "responseType": "post", "postedAt": "2026-01-01", "text": "post",
            "media": [{"id": media_id, "type": "photo", "canView": True,
                       "files": {"full": {"url": "https://example.invalid/image.jpg"}}}],
        }
        for media_id in media_ids
    ])
    return collection


def test_rows_from_several_models_have_unique_keys(monkeypatch):
    collections = {"1": {"collection": collection_for(1, [11, 12])}, "2": {"collection": collection_for(2, [21])}}
    monkeypatch.setattr(check, "check_user_dict", collections)
    monkeypatch.setattr(check, "ROWS", [])
    monkeypatch.setattr(check, "get_media_post_ids_downloaded", lambda **kwargs: [])

    async def gather():
        await check.row_gather("model1", 1)
        await check.row_gather("model2", 2)
        # A model listed twice is gathered twice.
        await check.row_gather("model1", 1)

    asyncio.run(gather())
    keys = [row["index"] for row in check.ROWS]
    assert len(keys) == len(set(keys)) == 3
    assert sorted(row["media_id"] for row in check.ROWS) == [11, 12, 21]


def check_areas(monkeypatch, value):
    parsed, _ = post_check.main(args=["--url", "model", "--check-area", value], standalone_mode=False)
    monkeypatch.setattr(settings, "get_settings", lambda: NS(**parsed))
    return check.get_areas()


def test_post_dates_use_a_24_hour_clock_and_flag_missing_dates(monkeypatch):
    collection = PostCollection(model_id=1, username="model1")
    photo = {"type": "photo", "canView": True, "files": {"full": {"url": "https://example.invalid/image.jpg"}}}
    collection.add_posts([
        {"id": 101, "responseType": "post", "postedAt": "2026-01-01T13:30:00+00:00", "media": [dict(photo, id=11)]},
        {"id": 102, "responseType": "post", "media": [dict(photo, id=12)]},
        {"id": 103, "responseType": "post", "media": [dict(photo, id=13)]},
    ])
    monkeypatch.setattr(check, "check_user_dict", {"1": {"collection": collection}})
    monkeypatch.setattr(check, "ROWS", [])
    monkeypatch.setattr(check, "get_media_post_ids_downloaded", lambda **kwargs: [])
    asyncio.run(check.row_gather("model1", 1))
    dates = {row["media_id"]: row["post_date"] for row in check.ROWS}
    assert dates == {11: "2026-01-01 13:30:00", 12: "Probably Deleted", 13: "Probably Deleted"}


def test_check_area_all_scans_the_post_areas(monkeypatch):
    areas = check_areas(monkeypatch, "All")
    assert {"Timeline", "Pinned", "Archived", "Streams"} <= set(areas)
    assert "All" not in areas


def test_check_area_all_can_add_labels(monkeypatch):
    assert "Labels" in check_areas(monkeypatch, "All,Labels")
