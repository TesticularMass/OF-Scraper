from contextlib import asynccontextmanager, nullcontext
from types import SimpleNamespace as NS

import ofscraper.commands.manual as manual


def test_manual_highlight_downloads_are_filed_as_highlights(monkeypatch):
    @asynccontextmanager
    async def session(**kwargs):
        yield object()

    async def highlight(post_id, c):
        # stories have no responseType of their own
        return [{"id": 9, "userId": 5, "media": []}]

    monkeypatch.setattr(manual.progress_utils, "setup_live", lambda *a, **k: nullcontext())
    monkeypatch.setattr(manual.progress_updater, "activity", NS(update_task=lambda **k: None))
    monkeypatch.setattr(manual.manager, "Manager", NS(session=NS(aget_ofsession=session)))
    monkeypatch.setattr(manual.highlights_, "get_individual_highlights", highlight)
    monkeypatch.setattr(
        manual.profile, "scrape_profile", lambda model_id: {"id": 5, "username": "model"}
    )
    monkeypatch.setattr(
        manual, "url_helper", lambda urls: ["https://onlyfans.com/stories/highlights/77"]
    )

    out = manual.process_urls(None)

    [post] = out[5]["collection"].posts
    assert post.responsetype == "Highlights"
