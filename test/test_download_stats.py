from ofscraper.classes.of.media import Media
from ofscraper.classes.of.posts import Post
from ofscraper.managers.stats import DownloadStats, StatsManager


def test_a_download_without_a_recorded_size_still_counts():
    # Known bad URLs are marked downloaded without fetching, so no size is set.
    post = Post({"id": 2, "responseType": "post", "media": []}, 1, "model")
    media = Media({"id": 1, "type": "photo", "canView": True}, 0, post)
    media.mark_download_succeeded()
    stats = DownloadStats("download")
    StatsManager()._update_download_stats_helper(stats, [media])
    assert (stats.photo_count, stats.total_bytes) == (1, 0)
