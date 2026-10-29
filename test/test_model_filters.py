import operator
from types import SimpleNamespace as NS
from unittest.mock import Mock

import arrow

import ofscraper.filters.models.date as date_filters
import ofscraper.filters.models.price as price_filters
import ofscraper.utils.settings as settings
from ofscraper.classes.of.models import Model
from ofscraper.filters.models.sort import sort_models_helper


def test_zero_maximum_price_keeps_only_free_models(monkeypatch):
    limits = {f"{kind}_price_{bound}": None for kind in ("promo", "regular", "renewal", "current") for bound in ("min", "max")}
    limits["current_price_max"] = 0
    monkeypatch.setattr(settings, "get_settings", lambda: NS(**limits))
    monkeypatch.setattr(price_filters, "trace_log_user", Mock())
    free, paid = NS(final_current_price=0), NS(final_current_price=10)
    assert price_filters.priceMinMaxFilters([free, paid]) == [free]


def test_hidden_last_seen_does_not_pass_date_filters(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(last_seen_after=arrow.utcnow().shift(days=-1)))
    monkeypatch.setattr(date_filters, "trace_log_user", Mock())
    hidden = Model({"id": 1, "username": "hidden", "lastSeen": None})
    assert date_filters._apply_date_filter([hidden], "last_seen_after", "final_last_seen", operator.ge) == []


def test_last_seen_sort_accepts_hidden_dates(monkeypatch):
    monkeypatch.setattr(settings, "get_settings", lambda: NS(sort="last-seen", desc=False))
    seen = Model({"id": 1, "username": "seen", "lastSeen": "2020-01-01T00:00:00+00:00"})
    hidden = Model({"id": 2, "username": "hidden", "lastSeen": None})
    assert sort_models_helper([hidden, seen]) == [seen, hidden]
