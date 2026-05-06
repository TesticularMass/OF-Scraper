import asyncio

import ofscraper.utils.context.exit as exit


def run(coro):
    def inner(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        if not loop.is_running():
            try:
                return loop.run_until_complete(coro(*args, **kwargs))
            except KeyboardInterrupt as E:
                with exit.DelayedKeyboardInterrupt():
                    pass
                raise E
            finally:
                # Always shut down async generators on completion to prevent leak.
                # is_running() guard removed: by definition the loop is not running
                # here (run_until_complete has returned).
                loop.run_until_complete(loop.shutdown_asyncgens())
        return coro(*args, **kwargs)

    return inner


def run_forever(coro):
    def inner(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        if not loop.is_running():
            try:
                asyncio.set_event_loop(loop)
                tasks = loop.run_until_complete(coro(*args, **kwargs))
                return tasks
            except RuntimeError:
                return coro(*args, **kwargs)
            except KeyboardInterrupt as E:
                with exit.DelayedKeyboardInterrupt():
                    try:
                        if tasks is not None:
                            tasks.cancel()
                            loop.run_forever()
                            tasks.exception()
                    except Exception:
                        None
                raise E
            except Exception as E:
                raise E
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
                asyncio.set_event_loop(None)
        return coro(*args, **kwargs)

    return inner
