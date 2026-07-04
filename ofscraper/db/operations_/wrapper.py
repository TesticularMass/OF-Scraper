import asyncio
import atexit
import logging
import pathlib
import sqlite3
from collections import abc
from concurrent.futures import ThreadPoolExecutor

import tenacity

import ofscraper.classes.placeholder as placeholder
import ofscraper.utils.context.exit as exit
import ofscraper.utils.of_env.of_env as of_env

log = logging.getLogger("shared")

# Shared pool with 1 worker to serialize DB writes and prevent "database is locked" errors
_DB_POOL = ThreadPoolExecutor(max_workers=1)
atexit.register(lambda: _DB_POOL.shutdown(wait=False))


def _is_network_path(db_path: pathlib.Path) -> bool:
    """Detect SMB/UNC network paths where WAL mode is unreliable."""
    resolved = str(db_path.resolve())
    return resolved.startswith("\\\\") or resolved.startswith("//")


def _configure_db_connection(conn, is_network: bool):
    """Apply PRAGMAs. Skip WAL and mmap on network paths — SMB breaks them."""
    if is_network:
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        # mmap and large cache_size are unsafe on network drives
    else:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA mmap_size=268435456;")
        conn.execute("PRAGMA cache_size=-32768;")
    conn.row_factory = sqlite3.Row


def operation_wrapper_async(func: abc.Callable):
    async def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        db_timeout = of_env.getattr("DATABASE_TIMEOUT")

        # Wrap the inner DB work with Tenacity to handle async/thread collisions gracefully
        @tenacity.retry(
            retry=tenacity.retry_if_exception_type(sqlite3.OperationalError),
            wait=tenacity.wait_random_exponential(multiplier=0.5, max=10),
            stop=tenacity.stop_after_attempt(5),
            reraise=True,
        )
        def _db_work():
            conn = None
            try:
                database_path = pathlib.Path(
                    kwargs.get("db_path", None)
                    or placeholder.databasePlaceholder().databasePathHelper(
                        kwargs.get("model_id"), kwargs.get("username")
                    )
                ).resolve()
                database_path.parent.mkdir(parents=True, exist_ok=True)

                conn = sqlite3.connect(
                    database_path, check_same_thread=False, timeout=db_timeout
                )

                _configure_db_connection(conn, _is_network_path(database_path))

                # grab the write lock
                conn.execute("BEGIN IMMEDIATE;")

                # Execute the database logic
                result = func(*args, **kwargs, conn=conn)
                conn.commit()  # Auto-commit if func succeeded without exception
                return result

            except Exception as E:
                log.debug(f"Database operation failed: {E}")
                raise E
            finally:
                if conn:
                    try:
                        conn.close()
                    except sqlite3.Error:
                        pass

        # Submit the safe retry block to the single-worker pool
        return await loop.run_in_executor(_DB_POOL, _db_work)

    return inner


def operation_wrapper(func: abc.Callable):
    # Apply Tenacity retry directly to the inner sync function
    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(sqlite3.OperationalError),
        wait=tenacity.wait_random_exponential(multiplier=0.5, max=10),
        stop=tenacity.stop_after_attempt(5),
        reraise=True,
    )
    def inner(*args, **kwargs):
        conn = None
        db_timeout = of_env.getattr("DATABASE_TIMEOUT")
        try:
            database_path = pathlib.Path(
                kwargs.get("db_path", None)
                or placeholder.databasePlaceholder().databasePathHelper(
                    kwargs.get("model_id"), kwargs.get("username")
                )
            ).resolve()
            database_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(
                database_path, check_same_thread=True, timeout=db_timeout
            )

            _configure_db_connection(conn, _is_network_path(database_path))

            conn.execute("BEGIN IMMEDIATE;")

            result = func(*args, **kwargs, conn=conn)
            conn.commit()  # Auto-commit if func succeeded without exception
            return result

        except sqlite3.OperationalError as E:
            log.info(f"Database is busy. Current timeout is {db_timeout}s.")
            raise E
        except KeyboardInterrupt as E:
            with exit.DelayedKeyboardInterrupt():
                raise E
        except Exception as E:
            raise E
        finally:
            if conn:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass

    return inner
