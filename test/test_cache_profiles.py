from types import SimpleNamespace as NS

from diskcache import Disk

import ofscraper.managers.profile as profile_module
import ofscraper.utils.cache.cache as cache
import ofscraper.utils.settings as settings


def test_switching_profiles_switches_the_cache(monkeypatch, tmp_path):
    args = NS(profile="first")
    monkeypatch.setattr(cache, "cache", None)
    monkeypatch.setattr(cache, "_disabled_due_to_error", False)
    monkeypatch.setattr(settings, "get_settings", lambda: NS(cached_disabled=False))
    monkeypatch.setattr(settings, "get_args", lambda *args_, **kwargs: args)
    monkeypatch.setattr(settings, "update_args", lambda new_args: None)
    monkeypatch.setattr(profile_module.profile_data, "get_active_profile", lambda: args.profile)
    monkeypatch.setattr(cache.data, "get_cache_mode", lambda: Disk)
    monkeypatch.setattr(cache.common_paths, "getcachepath", lambda: tmp_path / args.profile)

    cache.set("purchased_all", [111])
    profile_module.ProfileManager().switch_profile("second")
    assert cache.get("purchased_all") is None
    profile_module.ProfileManager().switch_profile("first")
    assert cache.get("purchased_all") == [111]
