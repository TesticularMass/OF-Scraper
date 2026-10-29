from types import SimpleNamespace as NS
from unittest.mock import Mock

import ofscraper.commands.scraper.scraper as scraper
import ofscraper.utils.settings as settings
from ofscraper.classes.of.models import Model
from ofscraper.commands.scraper.actions.subscribe import get_subscribable_models


def test_subscribe_batch_only_uses_selected_models(monkeypatch):
    selected, unselected = NS(name="selected"), NS(name="unselected")
    monkeypatch.setattr(settings, "get_settings", lambda: NS(actions=["subscribe"], sub_status=None))
    monkeypatch.setattr(scraper.manager, "Manager", NS(current_model_manager=NS(all_subs=[selected, unselected])))
    subscribe = Mock()
    monkeypatch.setattr(scraper.subscribe_action, "process_subscribe_batch", subscribe)
    scraper.scraperManager()._run_subscribe_batch([selected])
    subscribe.assert_called_once_with(models=[selected])


def test_paid_model_with_free_promotion_sends_the_promotion():
    promo = {"id": 44, "canClaim": True, "price": 0}
    model = Model({"id": 1, "username": "promo", "subscribePrice": 10, "promotions": [promo]})
    assert get_subscribable_models([model]) == [(model, promo)]


def test_free_model_subscribes_without_a_promotion():
    model = Model({"id": 2, "username": "free", "subscribePrice": 0})
    assert get_subscribable_models([model]) == [(model, None)]


def test_model_without_a_known_price_is_not_subscribed():
    model = Model({"id": 3, "username": "unknown"})
    assert get_subscribable_models([model]) == []
