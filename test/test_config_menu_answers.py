import pytest

import ofscraper.utils.config.data as data
import ofscraper.utils.config.schema as schema


# (section, key in the saved config, key the menu answers with, new answer)
MENU_ANSWERS = [
    ("advanced_options", "rotate_logs", "rotate_logs", False),
    ("advanced_options", "incremental_downloads", "incremental_downloads", False),
    ("download_options", "auto_resume", "auto_resume", False),
    ("file_options", "truncation_default", "truncation_default", False),
    ("file_options", "textlength", "textlength", 0),
    ("content_filter_options", "length_max", "length_max", 0),
    ("script_options", "post_script", "post_script", ""),
    ("file_options", "space_replacer", "space-replacer", "_"),
]


@pytest.mark.parametrize("section, key, answer_key, answer", MENU_ANSWERS)
def test_config_menu_answers_replace_the_saved_value(section, key, answer_key, answer):
    saved = schema.get_current_config_schema(False)
    saved[section][key] = {bool: True, int: 40, str: "/old/value"}[type(answer)]
    # the config menu saves its answers as top-level keys over the saved config
    config = {**saved, answer_key: answer}

    rewritten = schema.get_current_config_schema({"config": config})

    assert rewritten[section][key] == answer


def test_incremental_downloads_can_be_turned_off_in_config():
    # a saved false used to fall through to the legacy enable_auto_after key
    config = {"advanced_options": {"incremental_downloads": False}}
    assert data.get_incremental_downloads(config=config) is False
