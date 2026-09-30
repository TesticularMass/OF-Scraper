"""Create network event loops without changing the terminal UI's loop policy."""

import asyncio
import sys


def new_event_loop():
    # A global uvloop policy also affects prompt-toolkit. Its terminal reader
    # leaves the shared stdin/stdout descriptor nonblocking, breaking large
    # Rich writes. Keep uvloop scoped to our network work instead.
    if sys.platform == "linux":
        import uvloop

        return uvloop.new_event_loop()
    return asyncio.new_event_loop()
