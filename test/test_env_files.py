import os
from types import SimpleNamespace as NS

import ofscraper.utils.settings as settings


def test_env_files_from_the_command_line_are_loaded(monkeypatch, tmp_path):
    env_file = tmp_path / "custom.env"
    env_file.write_text("OFSC_TEST_ENV_FILE_VALUE=loaded\n")
    args = settings.get_args(copy=True)
    args.env_files = (str(env_file),)
    monkeypatch.setattr(settings.read_args, "retriveArgs", lambda: args)
    monkeypatch.setattr(settings, "settings", settings.settings)
    monkeypatch.setenv("OFSC_TEST_ENV_FILE_VALUE", "unset")

    merged = settings.setup_settings()

    assert os.environ["OFSC_TEST_ENV_FILE_VALUE"] == "loaded"
    assert merged.env_files == [str(env_file)]


def test_env_files_written_as_a_string_in_config_are_split(monkeypatch):
    monkeypatch.setattr(settings.config_data, "get_env_files", lambda: "a.env, b.env")
    assert settings._env_files(NS(env_files=None)) == ["a.env", "b.env"]
