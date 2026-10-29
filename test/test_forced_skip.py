import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import pytest

import ofscraper.commands.scraper.actions.download.managers.alt_download as alt_download
import ofscraper.commands.scraper.actions.download.managers.downloadmanager as downloadmanager
import ofscraper.commands.scraper.actions.utils.globals as common_globals
import ofscraper.utils.settings as settings
from ofscraper.classes.of.media import Media
from ofscraper.classes.of.posts import Post


@pytest.fixture
def limits(monkeypatch):
    monkeypatch.setattr(common_globals, "log", Mock())

    def set_limits(size_max=0, size_min=0, script_skips=False):
        monkeypatch.setattr(
            settings, "get_settings", lambda: NS(size_max=size_max, size_min=size_min, quality=None)
        )
        monkeypatch.setattr(downloadmanager, "skip_download_script", AsyncMock(return_value=script_skips))

    return set_limits


def video():
    post = Post({"id": 2, "responseType": "post", "media": []}, 1, "model")
    media = {"id": 1, "type": "video", "canView": True, "files": {"full": {"url": "https://cdn.example/a.mp4"}}}
    return Media(media, 0, post)


@pytest.mark.parametrize(
    "size_max, size_min, script_skips", [(3, 0, False), (0, 10, False), (0, 0, True)]
)
def test_a_file_skipped_on_purpose_is_reported_as_skipped(limits, size_max, size_min, script_skips):
    limits(size_max, size_min, script_skips)
    ele = video()
    assert asyncio.run(downloadmanager.DownloadManager()._check_forced_skip(ele, 5)) == 0
    # The downloaders report "forced_skipped" only for this media type;
    # anything else is counted as a failed download.
    assert ele.mediatype == "Forced_skipped"


def track(tmp_path, kind, size):
    path = tmp_path / f"{kind}.mp4"
    path.write_bytes(b"x" * size)
    return {"type": kind, "path": path, "total": size}


def test_drm_size_limits_judge_the_whole_file(limits, tmp_path):
    # A small audio track must not skip a file that is over the minimum.
    limits(size_min=10)
    manager, ele = alt_download.AltDownloadManager(), video()
    assert asyncio.run(manager._check_forced_skip(ele, 4)) is None
    audio, video_track = track(tmp_path, "audio", 4), track(tmp_path, "video", 20)
    assert asyncio.run(manager._media_item_post_process_alt(audio, video_track, ele, "model", 1)) is None
    assert ele.mediatype == "Videos"


def test_a_drm_file_under_the_minimum_is_skipped(limits, tmp_path):
    limits(size_min=30)
    audio, video_track = track(tmp_path, "audio", 4), track(tmp_path, "video", 20)
    result = asyncio.run(
        alt_download.AltDownloadManager()._media_item_post_process_alt(audio, video_track, video(), "model", 1)
    )
    assert result == ("forced_skipped", 0)
    assert not audio["path"].exists() and not video_track["path"].exists()


def test_a_drm_file_missing_a_track_is_a_failed_download(limits, tmp_path):
    limits()
    audio, video_track = track(tmp_path, "audio", 4), {"type": "video", "path": tmp_path / "none", "total": 0}
    result = asyncio.run(
        alt_download.AltDownloadManager()._media_item_post_process_alt(audio, video_track, video(), "model", 1)
    )
    assert result == ("skipped", 0)
    # kept so the next run can resume it
    assert audio["path"].exists()


def test_a_drm_track_over_the_maximum_skips_the_file(limits, monkeypatch, tmp_path):
    limits(size_max=10)
    downloaded = []

    async def download_track(self, item, c, ele):
        downloaded.append(item["type"])
        item["path"] = tmp_path / f"{item['type']}.part"
        item["total"] = 0 if await self._check_forced_skip(ele, 50) == 0 else 50
        return item

    monkeypatch.setattr(alt_download.AltDownloadManager, "_alt_download_downloader", download_track)
    monkeypatch.setattr(alt_download, "path_to_file_logger", Mock())
    monkeypatch.setattr(common_globals, "sem", asyncio.Semaphore(1), raising=False)
    monkeypatch.setattr(alt_download.placeholder, "Placeholders", lambda *a: NS(init=AsyncMock()))
    ele = NS(
        id=1, post_id=2, url=None, mpd="https://cdn.example/a.mpd", mediatype="Videos", add_size=Mock(),
        mpd_audio=asyncio.sleep(0, result={"type": "audio"}),
        mpd_video=asyncio.sleep(0, result={"type": "video"}),
    )
    result = asyncio.run(alt_download.AltDownloadManager().alt_download(None, ele, "model", 1))
    assert result == ("forced_skipped", 0)
    assert downloaded == ["audio"]
