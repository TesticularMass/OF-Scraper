import asyncio
from types import SimpleNamespace as NS

import ofscraper.classes.placeholder as placeholder


def test_text_files_accept_the_media_placeholders(monkeypatch, tmp_path):
    monkeypatch.setattr(placeholder, "log", NS(trace=print, debug=print))
    monkeypatch.setattr(placeholder.basePlaceholder, "create_variables_base", lambda self: None)
    monkeypatch.setattr(
        placeholder.manager, "Manager", NS(current_model_manager=NS(get_model=lambda name: None))
    )
    monkeypatch.setattr(placeholder.config_file, "open_config", lambda: {})
    monkeypatch.setattr(placeholder.settings, "get_args", lambda: {})
    monkeypatch.setattr(placeholder.data, "get_dirformat", lambda: "{model_username}/{download_type}")
    monkeypatch.setattr(placeholder.data, "get_fileformat", lambda: "{media_id}.{ext}")
    post = NS(
        id=7, username="model", model_id=5, value="free", date=None, responsetype="Timeline",
        modified_responsetype="Posts", label_string="None", file_sanitized_text="hello",
        text_trunicate=lambda text: text,
    )

    holder = placeholder.Textholders(post, "txt")

    assert asyncio.run(holder.getmediadir(root=tmp_path, create=False)) == tmp_path / "model" / "Normal"
    assert asyncio.run(holder.createfilename()) == "7.txt"
