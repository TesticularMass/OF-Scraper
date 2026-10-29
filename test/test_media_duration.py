from ofscraper.classes.of.media import Media
from ofscraper.classes.of.posts import Post


def test_a_fractional_duration_can_be_saved():
    post = Post({"id": 1, "media": [{"id": 2, "type": "video", "duration": 75.4}]}, 5, "model")
    # written to the media table with every scanned item
    assert Media(post.post_media[0], 0, post).duration_string == "00:00:01:15"
