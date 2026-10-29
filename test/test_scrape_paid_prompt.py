from contextlib import nullcontext
from types import SimpleNamespace as NS
from unittest.mock import Mock

import ofscraper.commands.scraper.scraper as scraper
import ofscraper.utils.settings as settings


def test_scrape_paid_runs_in_the_run_where_the_user_turned_it_on(monkeypatch):
    state = NS(actions=["download"], scrape_paid=False, users_first=False)
    monkeypatch.setattr(settings, "get_settings", lambda: state)

    def prepare(menu=False):
        # the menu asks "Scrape entire paid page" here and the user picks True
        state.scrape_paid = True
        return [], None

    scrape_paid_all = Mock()
    monkeypatch.setattr(scraper, "prepare", prepare)
    monkeypatch.setattr(scraper, "scrape_paid_all", scrape_paid_all)
    monkeypatch.setattr(scraper, "check_auth", Mock())
    monkeypatch.setattr(scraper, "final_action", Mock())
    monkeypatch.setattr(scraper, "scrape_context_manager", nullcontext)
    monkeypatch.setattr(scraper.progress_utils, "stop_live_screen", lambda **kwargs: nullcontext())
    monkeypatch.setattr(scraper.progress_utils, "setup_live", lambda *args, **kwargs: nullcontext())
    monkeypatch.setattr(scraper.scraperManager, "_process_users_actions_normal", Mock())

    scraper.scraperManager().runner(menu=True)
    scrape_paid_all.assert_called_once()
