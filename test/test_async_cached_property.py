import asyncio
import unittest

from ofscraper.utils.async_cached_property import async_cached_property


class Loader:
    def __init__(self):
        self.calls = 0
        self.failures_left = 1

    @async_cached_property
    async def value(self):
        self.calls += 1
        await asyncio.sleep(0)
        return self.calls

    @async_cached_property
    async def flaky(self):
        if self.failures_left:
            self.failures_left -= 1
            raise ValueError("first call fails")
        return "ok"


class AsyncCachedPropertyTest(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_awaits_run_getter_once(self):
        loader = Loader()
        results = await asyncio.gather(*(loader.value for _ in range(10)))
        self.assertEqual(results, [1] * 10)
        self.assertEqual(await loader.value, 1)
        self.assertEqual(loader.calls, 1)

    async def test_cache_is_per_instance(self):
        first, second = Loader(), Loader()
        await first.value
        self.assertEqual(await second.value, 1)
        self.assertEqual((first.calls, second.calls), (1, 1))

    async def test_exceptions_are_not_cached(self):
        loader = Loader()
        with self.assertRaises(ValueError):
            await loader.flaky
        self.assertEqual(await loader.flaky, "ok")

    def test_rejects_sync_getter(self):
        with self.assertRaises(TypeError):
            async_cached_property(lambda self: None)

