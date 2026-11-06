import asyncio
import errno
import logging
import subprocess

import aiohttp
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_random

import ofscraper.utils.of_env.of_env as of_env
from ofscraper.commands.scraper.actions.utils.retries import get_download_retries


def _is_transient_download(exc):
    """Decide whether a download failure is worth retrying.

    Permanent (not retried): cancelled/interrupted, out-of-space/read-only
    filesystem errors, HTTP 400/401/403/404/410, validation/ffmpeg failures,
    and the special SPACE_DOWNLOAD_MESSAGE.  Everything else, including
    generic exceptions such as a transient DRM-license failure, is retried
    with backoff; the session layer already owns 403-refresh behaviour.
    """
    if isinstance(exc, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
        return False
    # A 403 whose media signature was just refreshed deserves one more try.
    if getattr(exc, "retry_after_refresh", False):
        return True
    if str(exc) == of_env.getattr("SPACE_DOWNLOAD_MESSAGE"):
        return False
    if isinstance(exc, OSError) and exc.errno in (
        errno.ENOSPC,
        errno.EDQUOT,
        errno.EROFS,
        errno.EACCES,
    ):
        return False
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError, OSError)):
        return True
    if isinstance(exc, aiohttp.ClientError):
        if isinstance(exc, aiohttp.ClientResponseError):
            return exc.status in (408, 425, 429, 500, 502, 503, 504)
        return True
    if isinstance(exc, (ValueError, subprocess.CalledProcessError)):
        return False
    if "failed duration integrity check" in str(exc):
        return False
    return True


class download_retry(AsyncRetrying):
    def __init__(self, stop=None, wait=None, retry=None) -> None:
        stop = stop or stop_after_attempt(get_download_retries())
        wait = wait or wait_random(
            min=of_env.getattr("OF_MIN_WAIT_API"),
            max=of_env.getattr("OF_MAX_WAIT_API"),
        )
        retry = retry or retry_if_exception(_is_transient_download)

        def _log_retry(retry_state):
            logging.getLogger("shared").debug(
                f"Download interrupted/failed. Retrying in {retry_state.next_action.sleep:.2f}s "
                f"(Attempt {retry_state.attempt_number})"
            )

        super().__init__(
            stop=stop,
            wait=wait,
            retry=retry,
            reraise=True,
            before_sleep=_log_retry
        )
