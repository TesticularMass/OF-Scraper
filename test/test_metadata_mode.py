import asyncio
import contextvars
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest

import ofscraper.commands.metadata.manager as metadata_manager
import ofscraper.utils.settings as settings


def test_update_records_the_file_that_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(metadata="update", hash=False))
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    new.mkdir()
    (old / "old.jpg").write_bytes(b"file")
    placeholder = NS(trunicated_filepath=new / "new.jpg", trunicated_filedir=new, trunicated_filename="new.jpg")
    prev = {"directory": str(old), "filename": "old.jpg", "downloaded": 1, "size": None}
    manager = metadata_manager.MetaDataManager()
    recorded = Path(manager._metadata_dir_helper(placeholder, prev), manager._metadata_file_helper(placeholder, prev))
    assert recorded == old / "old.jpg"
    assert manager._metadata_downloaded_helper(placeholder, prev) == 1
    assert manager._metadata_size_helper(placeholder, prev) == 4


@pytest.fixture
def metadata_request(monkeypatch):
    monkeypatch.setattr(metadata_manager, "get_alt_params", lambda ele: {})
    monkeypatch.setattr(metadata_manager, "get_medialog", lambda ele: "media")
    monkeypatch.setattr(metadata_manager, "get_download_retries", lambda: 1)
    monkeypatch.setattr(metadata_manager.common_globals, "log", Mock())
    monkeypatch.setattr(metadata_manager.common_globals, "attempt", contextvars.ContextVar("attempt", default=0))

    def run(ele, content_type, read_body):
        @asynccontextmanager
        async def response(**kwargs):
            yield NS(headers={"content-type": content_type}, iter_chunked=read_body)

        return asyncio.run(metadata_manager.MetaDataManager()._metadata_helper(NS(requests_async=response), ele))

    return run


def test_protected_media_metadata_uses_mp4(metadata_request):
    async def manifest(size):
        yield b"<MPD/>"

    ele = NS(url=None, mpd="https://example.invalid/manifest.mpd", content_type="mp4")
    assert metadata_request(ele, "application/dash+xml", manifest)._ext == "mp4"


def test_metadata_lookup_does_not_download_the_file(metadata_request):
    ele = NS(url="https://example.invalid/image.jpg", mpd=None, content_type="jpg")
    body = Mock(side_effect=AssertionError("metadata only needs the response headers"))
    assert metadata_request(ele, "image/jpeg", body)._ext == "jpeg"
