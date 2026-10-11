import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import arrow

with patch("sys.argv", ["ofscraper"]):
    import ofscraper.__main__
    from ofscraper.data.api import archive, streams


AREAS = (
    (archive, "archivedNextEP", "scrape_archived_posts", "get_archived_media"),
    (streams, "streamsNextEP", "scrape_stream_posts", "get_streams_media"),
)


class ArchivedStreamScansTest(unittest.IsolatedAsyncioTestCase):
    async def test_page_scan_uses_area_endpoint_and_returns_posts(self):
        page = {"id": 17, "postedAtPrecise": "100"}
        for module, endpoint, scraper_name, _ in AREAS:
            with self.subTest(area=module.API):
                response = SimpleNamespace(
                    status=200,
                    json_=AsyncMock(return_value={"list": [page], "hasMore": False}),
                )
                context = AsyncMock()
                context.__aenter__.return_value = response
                session = Mock()
                session.requests_async.return_value = context
                template = f"https://example.test/{module.API.lower()}/{{}}/{{}}"
                with (
                    patch.object(module.of_env, "getattr", return_value=template),
                    patch.object(
                        module.settings,
                        "get_settings",
                        return_value=SimpleNamespace(before=None),
                    ),
                ):
                    pages = [
                        batch
                        async for batch in getattr(module, scraper_name)(
                            session, 5, "user", timestamp=90, is_last_chunk=True
                        )
                    ]
                self.assertEqual(pages, [[page]])
                self.assertEqual(
                    session.requests_async.call_args.kwargs["url"],
                    template.format(5, "90"),
                )

    async def test_after_anchor_is_oldest_missing_media(self):
        media = [
            {
                "media_id": 1,
                "post_id": 11,
                "posted_at": 200,
                "media_type": "video",
                "downloaded": 0,
                "unlocked": 1,
            },
            {
                "media_id": 2,
                "post_id": 22,
                "posted_at": 100,
                "media_type": "video",
                "downloaded": 0,
                "unlocked": 1,
            },
        ]
        for module, _, _, media_getter in AREAS:
            with self.subTest(area=module.API):
                with (
                    patch.object(module, "get_after_pre_checks", return_value=None),
                    patch.object(
                        module, media_getter, new_callable=AsyncMock, return_value=media
                    ),
                    patch.object(
                        module,
                        "get_media_ids_downloaded_model",
                        new_callable=AsyncMock,
                        return_value=set(),
                    ),
                    patch.object(
                        module,
                        "get_deleted_post_ids",
                        new_callable=AsyncMock,
                        return_value=set(),
                    ),
                    patch.object(
                        module.settings,
                        "get_settings",
                        return_value=SimpleNamespace(mediatypes=None),
                    ),
                ):
                    after = await module.get_after(5, "user")
                self.assertEqual(after, arrow.get(100).float_timestamp)

    async def test_batch_scan_deduplicates_posts_across_workers(self):
        async def pages(*batches):
            for batch in batches:
                yield batch

        for module, _, _, _ in AREAS:
            with self.subTest(area=module.API):
                progress = Mock()
                with patch.object(module.shared.progress_utils, "api", progress):
                    posts = await module.process_tasks_batch(
                        [
                            pages([{"id": 1}, {"id": 2}]),
                            pages([{"id": 2}, {"id": 3}]),
                        ]
                    )
                self.assertEqual({post["id"] for post in posts}, {1, 2, 3})
                self.assertEqual(len(posts), 3)
                progress.remove_overall_task.assert_called_once()

    async def test_missing_known_post_is_marked_deleted(self):
        page = {"id": 17, "postedAtPrecise": "100"}
        for module, _, scraper_name, _ in AREAS:
            with self.subTest(area=module.API):
                response = SimpleNamespace(
                    status=200,
                    json_=AsyncMock(return_value={"list": [page], "hasMore": False}),
                )
                context = AsyncMock()
                context.__aenter__.return_value = response
                session = Mock()
                session.requests_async.return_value = context
                with (
                    patch.object(
                        module.of_env,
                        "getattr",
                        return_value="https://example.test/{}/{}",
                    ),
                    patch.object(
                        module.settings,
                        "get_settings",
                        return_value=SimpleNamespace(before=None),
                    ),
                    patch.object(
                        module,
                        "mark_post_as_deleted",
                        new_callable=AsyncMock,
                    ) as mark_deleted,
                ):
                    batches = [
                        batch
                        async for batch in getattr(module, scraper_name)(
                            session,
                            5,
                            "user",
                            timestamp=90,
                            required_posts=[{"post_id": 99, "timestamp": 95}],
                            is_last_chunk=True,
                        )
                    ]
                self.assertEqual(batches, [[page]])
                mark_deleted.assert_awaited_once_with(
                    post_ids=[99], model_id=5, username="user"
                )

    def test_gap_worker_precedes_known_post_chunk(self):
        chunks = [[{"post_id": 11, "created_at": 100}]]
        for module, _, scraper_name, _ in AREAS:
            with self.subTest(area=module.API):
                scraper = Mock(side_effect=lambda *args, **kwargs: kwargs)
                with patch.object(module, scraper_name, scraper):
                    tasks = module.get_tasks(chunks, Mock(), 5, "user", 50)
                self.assertEqual(len(tasks), 2)
                self.assertEqual(tasks[0]["timestamp"], 50)
                self.assertEqual(tasks[0]["required_posts"][0]["post_id"], 11)
                self.assertEqual(tasks[1]["timestamp"], 100)
                self.assertTrue(tasks[1]["is_last_chunk"])


if __name__ == "__main__":
    unittest.main()
