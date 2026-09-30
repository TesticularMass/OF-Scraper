import contextlib
import logging
import sqlite3
import threading

from diskcache import Cache

import ofscraper.utils.config.data as data
import ofscraper.utils.paths.common as common_paths
import ofscraper.utils.settings as settings

cache = None
lock = threading.Lock()
log = logging.getLogger("shared")
_disabled_due_to_error = False
_UNAVAILABLE = object()


def _call(method, *args, **kwargs):
    """Close each thread's connection and reconnect once on a cache failure."""
    global cache, _disabled_due_to_error
    with lock:
        if settings.get_settings().cached_disabled or _disabled_due_to_error:
            return _UNAVAILABLE
        for attempt in range(2):
            try:
                if cache is None:
                    cache = Cache(common_paths.getcachepath(), disk=data.get_cache_mode())
                # DiskCache.close() only closes the calling thread's connection.
                # A single executor cleanup job cannot close other workers'.
                with contextlib.closing(cache):
                    return getattr(cache, method)(*args, **kwargs)
            except sqlite3.ProgrammingError:
                raise
            except sqlite3.DatabaseError as error:
                code = getattr(error, "sqlite_errorname", type(error).__name__)
                if attempt == 0:
                    log.warning(
                        "Cache %s failed (%s: %s); retrying with a fresh connection.",
                        method, code, error,
                    )
                else:
                    _disabled_due_to_error = True
                    log.warning(
                        "Cache %s failed again (%s: %s). Disabling the optional "
                        "cache for this run and fetching fresh data so models are "
                        "not skipped. Download-history databases are unchanged.",
                        method, code, error,
                    )
        return _UNAVAILABLE


def get(*args, **kwargs):
    result = _call("get", *args, **kwargs)
    if result is not _UNAVAILABLE:
        return result
    default = kwargs.get("default", args[1] if len(args) > 1 else None)
    expire_time = kwargs.get("expire_time", args[3] if len(args) > 3 else False)
    tag = kwargs.get("tag", args[4] if len(args) > 4 else False)
    if expire_time and tag:
        return default, None, None
    if expire_time or tag:
        return default, None
    return default


def set(*args, auto_close=True, **kwargs):
    # Keep the call signature, but always close on the owning thread rather
    # than relying on a later cleanup job running on the right worker.
    _call("set", *args, **kwargs)


def touch(*args, **kwargs):
    _call("touch", *args, **kwargs)


def close(*args, **kwargs):
    global _disabled_due_to_error
    with lock:
        if cache is not None:
            try:
                cache.close(*args, **kwargs)
            except sqlite3.ProgrammingError:
                raise
            except sqlite3.DatabaseError as error:
                if not _disabled_due_to_error:
                    log.warning(
                        "Cache cleanup failed (%s: %s); disabling the optional "
                        "cache for this run so model processing can continue.",
                        getattr(error, "sqlite_errorname", type(error).__name__), error,
                    )
                _disabled_due_to_error = True
