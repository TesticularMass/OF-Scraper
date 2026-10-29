import asyncio
import contextlib
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import arrow

import ofscraper.commands.metadata.metadata as metadata_command
import ofscraper.data.posts.post as post_module
import ofscraper.utils.settings as settings
from ofscraper.classes.of.posts import Post


def test_area_scans_record_how_far_back_they_reached(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(skip_unavailable_content=False, command="metadata", text=False))
    monkeypatch.setattr(post_module, "get_like_area", lambda: set())
    monkeypatch.setattr(post_module, "get_download_area", lambda: {"Timeline", "Archived"})
    monkeypatch.setattr(post_module, "get_final_posts_area", lambda: {"Timeline", "Archived"})
    monkeypatch.setattr(post_module.progress_utils, "setup_live", lambda *args, **kwargs: contextlib.nullcontext())
    timeline = [Post({"id": n, "postedAt": date, "media": []}, 1, "model", "Timeline")
                for n, date in ((1, "2026-03-01"), (2, "2026-01-15"))]
    monkeypatch.setattr(post_module, "process_timeline_posts", AsyncMock(return_value=(timeline, "Timeline")))
    # A failed area scan returns None.
    monkeypatch.setattr(post_module, "process_archived_posts", AsyncMock(return_value=None))
    collection = asyncio.run(post_module.process_tasks(1, "model", NS(active=True), c=None))
    assert collection.scanned_areas == {"Timeline": arrow.get("2026-01-15").float_timestamp}


def test_mark_stray_locks_only_media_a_completed_scan_no_longer_returns(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(mark_stray=True, post_id=None))
    monkeypatch.setattr(settings, "get_args", lambda: NS(after=None, before=arrow.get("2030-01-01")))
    monkeypatch.setattr(metadata_command.progress_updater.activity, "update_task", Mock())

    def rows(*entries):
        return [
            {"media_id": media_id, "posted_at": arrow.get(date).float_timestamp, "downloaded": 0, "unlocked": 1}
            for media_id, date in entries
        ]

    monkeypatch.setattr(metadata_command, "get_timeline_media", AsyncMock(return_value=rows(
        (1, "2026-02-01"), (2, "2026-02-01"), (3, "2026-02-01"), (4, "2025-06-01"))))
    monkeypatch.setattr(metadata_command, "get_archived_media", AsyncMock(return_value=rows((5, "2026-02-01"))))
    monkeypatch.setattr(metadata_command, "get_messages_media", AsyncMock(return_value=rows((6, "2026-02-01"))))
    lock = Mock()
    monkeypatch.setattr(metadata_command, "batch_set_media_downloaded", lock)
    collection = NS(
        # Media 2 came back from the API; only a user filter dropped it from the worklist.
        all_media=[NS(id=1), NS(id=2)],
        # Timeline reached back to January 2026, Archived failed and Messages returned nothing.
        scanned_areas={"Timeline": arrow.get("2026-01-01").float_timestamp, "Messages": None},
    )
    asyncio.run(metadata_command.MetadataCommandManager()._metadata_stray_media("model", 1, collection))
    lock.assert_called_once()
    assert [row["media_id"] for row in lock.call_args.args[0]] == [3]


def test_mark_stray_skips_scans_limited_to_specific_posts(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(mark_stray=True, post_id=[123]))
    timeline = AsyncMock(return_value=[])
    monkeypatch.setattr(metadata_command, "get_timeline_media", timeline)
    collection = NS(all_media=[], scanned_areas={"Timeline": 0.0})
    asyncio.run(metadata_command.MetadataCommandManager()._metadata_stray_media("model", 1, collection))
    timeline.assert_not_awaited()
