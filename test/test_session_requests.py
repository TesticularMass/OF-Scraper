import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import web

from ofscraper.managers.sessionmanager.sessionmanager import sessionManager


def make_session(**kwargs):
    session = sessionManager(retries=3, wait_min=0, wait_max=0, log=Mock(), **kwargs)
    idle = NS(async_do_sleep=AsyncMock(return_value=False), do_sleep=lambda: False)
    session._rate_limit_sleeper = idle
    session._forbidden_sleeper = idle
    session._get_ssl_context = lambda: False
    return session


def test_sync_request_honours_retry_override():
    session = make_session()
    session._httpx_funct = Mock(side_effect=OSError("offline"))
    with pytest.raises(OSError):
        with session.requests("https://example.invalid", retries=1):
            pass
    assert session._httpx_funct.call_count == 1


def test_async_request_honours_retry_override():
    session = make_session()
    session._aio_funct = AsyncMock(side_effect=OSError("offline"))

    async def request():
        async with session.requests_async("https://example.invalid", retries=1):
            pass

    with pytest.raises(OSError):
        asyncio.run(request())
    assert session._aio_funct.call_count == 1


def test_cancelled_request_is_not_retried():
    session = make_session()
    session._aio_funct = AsyncMock(side_effect=[asyncio.CancelledError(), NS(ok=True)])

    async def request():
        async with session.requests_async("https://example.invalid"):
            pass

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(request())
    assert session._aio_funct.call_count == 1


def test_leaving_a_response_unread_frees_its_connection():
    async def exercise():
        finish_stream = asyncio.Event()

        async def stream(request):
            response = web.StreamResponse(headers={"Content-Length": str(10 * 1024 * 1024)})
            await response.prepare(request)
            await response.write(b"x" * 1024)
            await finish_stream.wait()
            return response

        async def small(request):
            return web.Response(text="ok")

        app = web.Application()
        app.router.add_get("/stream", stream)
        app.router.add_get("/small", small)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        base = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
        session = make_session(limit=1)

        async def read_small():
            async with session.requests_async(f"{base}/small") as response:
                return await response.text_()

        try:
            async with session:
                # Size-filtered downloads leave the context without reading the body.
                async with session.requests_async(f"{base}/stream") as response:
                    pass
                assert response.closed
                # The pool holds one connection, so this waits forever if it is still held.
                assert await asyncio.wait_for(read_small(), timeout=5) == "ok"
        finally:
            finish_stream.set()
            await runner.cleanup()

    asyncio.run(exercise())
