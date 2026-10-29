import asyncio
from types import SimpleNamespace as NS

import ofscraper.classes.of.media as media_
import ofscraper.classes.of.posts as posts_
import ofscraper.scripts.naming_script as naming


def test_naming_script_runs_for_media_without_a_date(monkeypatch, tmp_path):
    script = tmp_path / "name.sh"
    script.write_text("")
    payloads = []

    async def run(cmd, input=None, **kwargs):
        payloads.append(input)
        return NS(stdout="custom.jpg")

    monkeypatch.setattr(naming.settings, "get_settings", lambda: NS(naming_script=str(script)))
    monkeypatch.setattr(naming, "async_run", run)
    monkeypatch.setattr(posts_.data, "responsetype", lambda: {})
    # profile media is dated by the join date, which some accounts hide
    post = posts_.Post({"id": 1, "media": [{"id": 2, "type": "photo"}]}, 5, "model", responsetype="Profile")
    media = media_.Media(post.post_media[0], 0, post)

    assert asyncio.run(naming.naming_script(tmp_path, "file.jpg", media)) == "custom.jpg"
    assert '"date": "unknown_date"' in payloads[0]
