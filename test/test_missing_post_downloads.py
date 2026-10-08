from contextlib import closing
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

with patch('sys.argv', ['ofscraper']):
    import ofscraper.__main__
    from ofscraper.commands.scraper.actions.download.managers import alt_download as alt
    from ofscraper.db.operations_ import posts


class MissingPostDownloadsTest(unittest.IsolatedAsyncioTestCase):
    async def test_zero_bytes_never_marked_downloaded(self):
        downloader = alt.AltDownloadManager()
        downloader._force_download = AsyncMock()
        result = await downloader._media_item_post_process_alt(
            {'total': 0}, {'total': 0}, SimpleNamespace(mediatype='Videos'), 'model', 1)
        self.assertEqual(result, ('skipped', 0))
        downloader._force_download.assert_not_awaited()

    async def test_signed_manifest_resolves_to_track_and_rejects_xml(self):
        downloader = alt.AltDownloadManager()
        downloader._alt_attempt_get = Mock(return_value=Mock(get=Mock(return_value=1)))
        downloader._get_resume_size = Mock(return_value=0)
        downloader._get_resume_header = Mock(return_value=None)
        downloader._total_change_helper = AsyncMock()
        downloader._set_data = AsyncMock()
        downloader._check_forced_skip = AsyncMock(return_value=0)
        ele = SimpleNamespace(mpd='https://cdn.example/files/video.mpd?tag=2', hls_header='', id=1, post_id=2)
        context = AsyncMock()
        context.__aenter__.return_value = SimpleNamespace(status=200, headers={'content-type': 'application/dash+xml'})
        session = Mock()
        session.requests_async.return_value = context
        with (
            patch.object(alt.common_globals, 'log', Mock()),
            patch.object(alt, 'get_medialog', return_value='test'),
            patch.object(alt, 'get_alt_params', return_value={}),
            patch.object(alt.auth_requests, 'get_cookies_str', return_value=''),
            patch.object(alt, 'temp_file_logger'),
        ):
            with self.assertRaisesRegex(ValueError, 'manifest'):
                await downloader._send_req_inner(session, ele, {'origname': 'video_1080.mp4', 'total': None}, SimpleNamespace(tempfilepath=Path('/tmp/unused')))
        self.assertEqual(session.requests_async.call_args.kwargs['url'], 'https://cdn.example/files/video_1080.mp4')
        downloader._set_data.assert_not_awaited()

    def test_pinned_posts_are_not_timeline_gap_candidates(self):
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.execute('create table posts (created_at real, post_id int, archived int, model_id int, is_deleted int, pinned int)')
            conn.executemany('insert into posts values (100, ?, 0, 1, 0, ?)', [(1, 0), (2, 1), (3, None)])
            self.assertEqual({r[1] for r in conn.execute(posts.timelinePostInfo, (1,))}, {1, 3})
