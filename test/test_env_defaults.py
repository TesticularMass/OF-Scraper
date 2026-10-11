import os
import unittest
from unittest.mock import patch

from ofscraper.utils.of_env import get_all_configs


class EnvironmentDefaultsTest(unittest.TestCase):
    def tearDown(self):
        get_all_configs(forced=True)

    def test_forced_reload_preserves_value_types_and_static_choices(self):
        overrides = {
            "OFSC_API_CHECK_NUM_TRIES": "7",
            "OFSC_CDM_SESSION_SLEEP_INIT": "3.25",
            "OFSC_SHOW_AVATAR": "false",
            "OFSC_SUPRESS_OUTPUTS": "ERROR, WARNING",
            "OFSC_PROMPT_DATE_FORMAT": "DD/MM/YYYY",
        }
        with patch.dict(os.environ, overrides):
            config = get_all_configs(forced=True)

        self.assertEqual(config["API_CHECK_NUM_TRIES"], 7)
        self.assertEqual(config["CDM_SESSION_SLEEP_INIT"], 3.25)
        self.assertIs(config["SHOW_AVATAR"], False)
        self.assertEqual(config["SUPRESS_OUTPUTS"], {"ERROR", "WARNING"})
        self.assertEqual(config["PROMPT_DATE_FORMAT"], "DD/MM/YYYY")
        self.assertEqual(config["mainPromptChoices"]["Quit"], "quit")

    def test_cached_values_change_only_on_forced_reload(self):
        with patch.dict(os.environ, {"OFSC_PROMPT_DATE_FORMAT": "FIRST"}):
            first = get_all_configs(forced=True)
        with patch.dict(os.environ, {"OFSC_PROMPT_DATE_FORMAT": "SECOND"}):
            self.assertIs(get_all_configs(), first)
            self.assertEqual(
                get_all_configs(forced=True)["PROMPT_DATE_FORMAT"], "SECOND"
            )


if __name__ == "__main__":
    unittest.main()
