import errno
import unittest
from unittest.mock import MagicMock, patch

# Import via the normal entry point to initialize the application's imports.
with patch("sys.argv", ["ofscraper"]):
    import ofscraper.__main__
    import ofscraper.utils.menu as menu


class MenuTerminalErrorsTest(unittest.TestCase):
    def test_terminal_failures_are_not_retried(self):
        for error in (
            BlockingIOError(errno.EAGAIN, "write could not complete without blocking"),
            BrokenPipeError(errno.EPIPE, "broken pipe"),
            EOFError(),
        ):
            with self.subTest(error=type(error).__name__):
                with (
                    patch.object(menu.console, "get_shared_console", return_value=MagicMock()),
                    patch.object(menu.prompts, "main_prompt", side_effect=[error, "quit"]) as prompt,
                ):
                    with self.assertRaises(type(error)):
                        menu.main_menu_action()
                    self.assertEqual(prompt.call_count, 1)

    def test_successful_action_returns_to_menu_then_quits(self):
        with (
            patch.object(menu.console, "get_shared_console", return_value=MagicMock()),
            patch.object(menu.prompts, "main_prompt", side_effect=["action", "quit"]) as prompt,
            patch.object(menu.prompts, "action_prompt", return_value="download"),
            patch("ofscraper.commands.scraper.scraper.scraperManager") as scraper,
        ):
            self.assertTrue(menu.main_menu_action())
            scraper.return_value.runner.assert_called_once_with(menu=True)
            self.assertEqual(prompt.call_count, 2)


if __name__ == "__main__":
    unittest.main()
