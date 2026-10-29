from ofscraper.classes.of import posts as posts_


def test_messages_use_the_configured_message_folder(monkeypatch):
    # the config, its menu and the defaults all name this key "message"
    monkeypatch.setattr(posts_.data, "responsetype", lambda: {"message": "Chats"})
    post = posts_.Post({"id": 1, "responseType": "message"}, 5, "model")
    assert post.modified_responsetype == "Chats"
