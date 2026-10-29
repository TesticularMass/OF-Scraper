import asyncio
from functools import partial
from unittest.mock import Mock

from tenacity import stop_after_attempt, wait_none

import ofscraper.commands.scraper.actions.download.managers.alt_download as alt_download
import ofscraper.commands.scraper.actions.utils.globals as common_globals
from ofscraper.commands.scraper.actions.download.utils.retries import download_retry


def test_a_retry_only_decrypts_the_tracks_still_encrypted(monkeypatch):
    monkeypatch.setattr(common_globals, "log", Mock())
    monkeypatch.setattr(
        alt_download, "download_retry", partial(download_retry, stop=stop_after_attempt(3), wait=wait_none())
    )
    decrypted = []

    async def un_encrypt(item, c, ele):
        if item["type"] == "video" and "video failed" not in decrypted:
            decrypted.append("video failed")
            raise Exception("license server hiccup")
        decrypted.append(item["type"])
        return item

    monkeypatch.setattr(alt_download.keyhelpers, "un_encrypt", un_encrypt)
    audio, video = {"type": "audio"}, {"type": "video"}
    asyncio.run(alt_download.AltDownloadManager()._media_item_keys_alt(None, audio, video, None))
    # Decrypting the audio again would hand ffmpeg its own output as input.
    assert decrypted == ["audio", "video failed", "video"]
