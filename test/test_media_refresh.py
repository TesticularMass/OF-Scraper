import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

from ofscraper.classes.of.media import Media
from ofscraper.classes.of.posts import Post


def test_refreshed_media_downloads_from_the_new_url():
    old = {"id": 7, "type": "photo", "canView": True, "files": {"full": {"url": "https://example.invalid/old.jpg"}}}
    new = dict(old, files={"full": {"url": "https://example.invalid/new.jpg"}})
    post = Post({"id": 8, "responseType": "post", "media": [old]}, 1, "model")
    media = Media(old, 0, post)
    assert media.url.endswith("old.jpg")

    @asynccontextmanager
    async def response(**kwargs):
        yield NS(json_=AsyncMock(return_value={"id": 8, "media": [new]}))

    assert asyncio.run(media.refresh_media(NS(requests_async=response)))
    assert media.url.endswith("new.jpg")
