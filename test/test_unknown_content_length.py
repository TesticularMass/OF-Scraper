import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import ofscraper.commands.scraper.actions.download.managers.downloadmanager as downloadmanager
import ofscraper.commands.scraper.actions.download.managers.main_download as main_download
import ofscraper.commands.scraper.actions.utils.globals as common_globals
import ofscraper.utils.settings as settings


def _download_without_content_length(monkeypatch, tmp_path, size_max=0):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(
        auto_resume=False, size_max=size_max, size_min=0, download_limit=0, command="scraper",
    ))
    monkeypatch.setattr(common_globals, "log", Mock())
    monkeypatch.setattr(common_globals, "attempt", Mock(get=Mock(return_value=1)))
    monkeypatch.setattr(main_download, "send_chunk_msg", Mock())
    monkeypatch.setattr(main_download.common_logs, "path_to_file_logger", Mock())
    monkeypatch.setattr(downloadmanager, "skip_download_script", AsyncMock(return_value=False))
    downloader = main_download.MainDownloadManager()
    downloader._set_data = AsyncMock()
    downloader._add_download_job_task = AsyncMock()
    downloader._remove_download_job_task = AsyncMock()
    downloader._total_change_helper = AsyncMock()

    async def body(chunk_size):
        yield b"12345"

    # A chunked response: the body arrives without a content-length header.
    @asynccontextmanager
    async def requests_async(**kwargs):
        yield NS(status=200, headers={"content-type": "image/jpeg"}, iter_chunked=body)

    temp = NS(tempfilepath=tmp_path / "photo.part")
    ele = NS(id=1, post_id=2, url="https://cdn.example/photo.jpg", mediatype="Images", filename="photo")
    total, path, _ = asyncio.run(
        downloader._send_req_inner(NS(requests_async=requests_async), ele, temp, placeholderObj=Mock())
    )
    return total, path, ele


def test_a_file_sent_without_a_content_length_downloads(monkeypatch, tmp_path):
    total, path, _ = _download_without_content_length(monkeypatch, tmp_path)
    assert total == 5
    assert path.read_bytes() == b"12345"


def test_size_limits_apply_once_the_size_is_known(monkeypatch, tmp_path):
    total, path, ele = _download_without_content_length(monkeypatch, tmp_path, size_max=3)
    assert total == 0
    assert not path.exists()
    assert ele.mediatype == "Forced_skipped"
