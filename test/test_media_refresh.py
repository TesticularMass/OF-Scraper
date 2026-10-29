import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

import ofscraper.utils.of_env.of_env as of_env
from ofscraper.classes.of.media import Media
from ofscraper.classes.of.posts import Post

OLD = {"id": 7, "type": "photo", "canView": True, "files": {"full": {"url": "https://example.invalid/old.jpg"}}}
NEW = dict(OLD, files={"full": {"url": "https://example.invalid/new.jpg"}})


def session(response, urls):
    @asynccontextmanager
    async def requests_async(url=None, **kwargs):
        urls.append(url)
        yield NS(json_=AsyncMock(return_value=response))

    return NS(requests_async=requests_async)


def refresh(post, response):
    media = Media(OLD, 0, Post(post, 1, "model", responsetype=post.pop("area", None)))
    urls = []
    return media, asyncio.run(media.refresh_media(session(response, urls))), urls


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


@pytest.mark.parametrize("area", ["Stories", "Highlights"])
def test_a_story_is_refreshed_by_its_story_id(area):
    media, refreshed, urls = refresh({"id": 8, "media": [OLD], "area": area}, {"id": 8, "media": [NEW]})
    assert refreshed and media.url.endswith("new.jpg")
    assert urls == [of_env.getattr("storiesSPECIFIC").format(8)]


@pytest.mark.parametrize("area", ["Streams", "Paid"])
def test_streams_and_purchased_posts_can_be_refreshed(area):
    post = {"id": 8, "responseType": "post", "media": [OLD], "area": area}
    media, refreshed, urls = refresh(post, {"id": 8, "media": [NEW]})
    assert refreshed and media.url.endswith("new.jpg")
    assert urls == [of_env.getattr("INDIVIDUAL_TIMELINE").format(8)]


def test_a_purchased_message_is_found_among_the_returned_messages():
    post = {"id": 8, "responseType": "message", "media": [OLD], "area": "Paid"}
    other = {"id": 9, "media": [dict(NEW, id=70)]}
    media, refreshed, _ = refresh(post, {"list": [other, {"id": 8, "media": [NEW]}]})
    assert refreshed and media.url.endswith("new.jpg")


def test_a_refresh_without_this_media_changes_nothing():
    post = {"id": 8, "responseType": "message", "media": [OLD], "area": "Messages"}
    media, refreshed, _ = refresh(post, {"list": [{"id": 9, "media": [dict(NEW, id=70)]}]})
    assert not refreshed
    assert media.post.id == 8 and media.url.endswith("old.jpg")
