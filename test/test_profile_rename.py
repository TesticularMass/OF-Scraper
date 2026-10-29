from types import SimpleNamespace as NS

import ofscraper.managers.profile as profile


def test_renaming_a_profile_follows_short_names_in_config_and_args(monkeypatch, tmp_path):
    (tmp_path / "main_profile").mkdir()
    saved = {}
    args = NS(profile="main")
    monkeypatch.setattr(profile.common_paths, "get_config_home", lambda: tmp_path)
    # "main" and "main_profile" name the same folder
    monkeypatch.setattr(profile.data, "get_current_config_profile", lambda: "main")
    monkeypatch.setattr(profile.config_, "update_config", lambda key, value: saved.update({key: value}))
    monkeypatch.setattr(profile.settings, "get_args", lambda: args)
    monkeypatch.setattr(profile.settings, "update_args", lambda new: None)
    monkeypatch.setattr(profile.cache, "reset", lambda: None)

    profile.ProfileManager().rename_profile("main_profile", "work_profile")

    assert (tmp_path / "work_profile").is_dir()
    assert saved == {"main_profile": "work_profile"}
    assert args.profile == "work_profile"
