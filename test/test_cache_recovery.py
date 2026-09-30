import sqlite3
import asyncio
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from diskcache import Cache

with patch('sys.argv', ['ofscraper']):
    import ofscraper.__main__
    import ofscraper.utils.cache.cache as cache_module
    from ofscraper.commands.utils.command import CommandManager


class CacheRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(cache_module.settings, 'get_settings', return_value=SimpleNamespace(cached_disabled=False)))
        self.enterContext(patch.object(cache_module, 'cache', None))
        self.enterContext(patch.object(cache_module, '_disabled_due_to_error', False, create=True))

    def test_read_connections_close_in_the_thread_that_opened_them(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = Cache(directory)
            backend.set('key', 'value')
            backend.close()
            cache_module.cache = backend
            def read():
                self.assertEqual(cache_module.get('key'), 'value')
                self.assertIsNone(getattr(backend._local, 'con', None))
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda _: read(), range(20)))

    def test_failed_read_reconnects_once(self):
        backend = cache_module.cache = Mock()
        backend.get.side_effect = [sqlite3.OperationalError('locking protocol'), 'recovered']
        self.assertEqual(cache_module.get('key'), 'recovered')
        self.assertEqual(backend.get.call_count, 2)
        self.assertGreaterEqual(backend.close.call_count, 2)

    def test_persistent_failure_does_not_skip_subsequent_models(self):
        backend = cache_module.cache = Mock()
        backend.get.side_effect = sqlite3.OperationalError('disk I/O error')
        self.assertEqual(cache_module.get('model_backup', default=123), 123)
        self.assertEqual(cache_module.get('next_model_backup', default=456), 456)
        cache_module.set('key', 'value')
        cache_module.touch('key')
        self.assertEqual(backend.get.call_count, 2)
        backend.set.assert_not_called()
        backend.touch.assert_not_called()

    def test_close_does_not_open_an_unused_cache(self):
        with patch.object(cache_module, 'Cache') as factory:
            cache_module.close()
            factory.assert_not_called()

    def test_programming_errors_are_not_hidden(self):
        backend = cache_module.cache = Mock()
        backend.get.side_effect = TypeError('bad argument')
        with self.assertRaises(TypeError):
            cache_module.get('key')

    def test_model_loop_continues_processing_after_cache_failure(self):
        backend = cache_module.cache = Mock()
        backend.get.side_effect = sqlite3.OperationalError('locking protocol')
        command = CommandManager()
        command._data_helper = Mock()
        command._avatar_helper = Mock()
        action = AsyncMock()
        async def retrieve(model, c):
            self.assertEqual(cache_module.get(f'{model}_db_backup', default=123), 123)
            return f'posts-{model}'
        with (
            patch('ofscraper.commands.utils.command.post_media_process', side_effect=retrieve),
            patch('ofscraper.commands.utils.command.progress_updater.activity.update_user'),
        ):
            asyncio.run(command._process_users_normal([1, 2, 3], AsyncMock(), action))
        self.assertEqual(action.await_count, 3)
        self.assertEqual(backend.get.call_count, 2)

    def test_failed_cleanup_does_not_abort_a_model(self):
        backend = cache_module.cache = Mock()
        backend.close.side_effect = sqlite3.OperationalError('disk I/O error')
        cache_module.close()
        self.assertEqual(cache_module.get('next', default=456), 456)
        backend.get.assert_not_called()

    def test_failed_writes_and_touches_are_retried(self):
        for method in ('set', 'touch'):
            with self.subTest(method=method):
                backend = cache_module.cache = Mock()
                getattr(backend, method).side_effect = [sqlite3.OperationalError('locking protocol'), True]
                getattr(cache_module, method)('key', 123)
                self.assertEqual(getattr(backend, method).call_count, 2)

    def test_disabled_cache_preserves_get_result_shape(self):
        cache_module._disabled_due_to_error = True
        self.assertEqual(cache_module.get('key', 123), 123)
        self.assertEqual(cache_module.get('key', default=123, expire_time=True, tag=True), (123, None, None))


if __name__ == '__main__':
    unittest.main()
