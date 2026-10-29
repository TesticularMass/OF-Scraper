from types import SimpleNamespace as NS

import ofscraper.data.api.labels as labels


def test_labels_scan_caches_the_labelled_posts_for_check_mode(monkeypatch):
    found = [{"id": 1, "name": "fav", "posts": [{"id": 10}, {"id": 11}]}]
    cached = []

    async def label_names(model_id, c=None):
        return [{"id": 1, "name": "fav"}]

    async def label_posts(labels_, model_id, c=None):
        return found

    monkeypatch.setattr(labels, "get_labels_data", label_names)
    monkeypatch.setattr(labels, "get_posts_for_labels", label_posts)
    monkeypatch.setattr(labels.settings, "get_settings", lambda: NS(label=None))
    monkeypatch.setattr(labels, "update_check", lambda data, *args: cached.append(data))

    assert labels.get_labels(5) == found
    # post_check reads this cache back as posts
    assert cached == [[{"id": 10}, {"id": 11}]]
