import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import ofscraper.data.api.pinned as pinned


def test_pinned_scan_stops_when_a_page_brings_nothing_new(monkeypatch):
    monkeypatch.setattr(pinned.progress_utils.api, "add_job_task", Mock())
    monkeypatch.setattr(pinned.progress_utils.api, "remove_job_task", Mock())
    requests = []

    # The pinned endpoint takes no offset, so every page is the same page.
    @asynccontextmanager
    async def requests_async(url=None, **kwargs):
        requests.append(url)
        if len(requests) > 5:
            raise AssertionError("the scan kept requesting the same page")
        yield NS(status=200, json_=AsyncMock(return_value={"list": [{"id": 1}], "hasMore": True}))

    async def scan():
        return [batch async for batch in pinned.scrape_pinned_posts(NS(requests_async=requests_async), 1)]

    assert asyncio.run(scan()) == [[{"id": 1}]]
