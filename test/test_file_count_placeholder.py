from types import SimpleNamespace as NS

import ofscraper.classes.placeholder as placeholder


def test_the_media_count_goes_before_the_extension_only(monkeypatch):
    monkeypatch.setattr(placeholder.data, "get_fileformat", lambda: "{text}.{ext}")
    ele = NS(count=2, responsetype="Timeline", _post=NS(post_media=[{}, {}]))
    name = placeholder.Placeholders(ele, "jpg")._addcount(ele, "Hello. World.jpg")
    assert name == "Hello. World_2.jpg"
