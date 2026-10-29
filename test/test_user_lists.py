import ofscraper.utils.settings as settings
from ofscraper.prompts.utils import prompt_helpers


def test_lists_from_config_match_case_insensitively(monkeypatch):
    args = settings.get_args(copy=True)
    args.userlist, args.blacklist = [], []
    monkeypatch.setattr(settings.read_args, "retriveArgs", lambda: args)
    monkeypatch.setattr(settings.config_data, "get_default_userlist", lambda: "VIP, Main")
    monkeypatch.setattr(settings.config_data, "get_default_blacklist", lambda: ["Muted"])

    merged = settings.merged_settings()

    assert merged.userlist == ["vip", "main"]
    assert merged.blacklist == ["muted"]


def test_list_editor_returns_only_lowercase_list_names():
    assert prompt_helpers.user_list("main,VIP\nFans, ") == ["main", "vip", "fans"]
