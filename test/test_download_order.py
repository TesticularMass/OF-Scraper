import asyncio
from collections import deque
from types import SimpleNamespace as NS
from unittest.mock import Mock

import ofscraper.commands.scraper.actions.download.run as run
import ofscraper.commands.scraper.actions.utils.globals as common_globals


def test_media_downloads_in_the_sorted_order(monkeypatch):
    monkeypatch.setattr(common_globals, "log", Mock())
    monkeypatch.setattr(common_globals, "total_bytes", 0, raising=False)
    monkeypatch.setattr(run, "log_download_progress", Mock())
    monkeypatch.setattr(run.progress_updater.download, "update_overall_task", Mock())
    order = []

    async def download(c, ele, model_id, username):
        order.append(ele.id)
        return "images", 0

    monkeypatch.setattr(run, "download", download)
    # final_media_sort has already put the media in the order the user chose
    medialist = [NS(id=n, mark_download_succeeded=Mock()) for n in (1, 2, 3)]
    aws = deque((None, ele, 1, "model") for ele in medialist)
    asyncio.run(run.consumer(aws, None, medialist, asyncio.Lock()))
    assert order == [1, 2, 3]
