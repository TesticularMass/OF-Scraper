"""Create event loops without changing the terminal UI's loop policy."""

import asyncio


def new_event_loop():
    # Use the standard loop for downloads as well as prompts. uvloop's native
    # Linux I/O polling aborted a long-running download in uv__epoll_ctl_flush;
    # SIGABRT bypasses Python exception handling and normal resource cleanup.
    return asyncio.new_event_loop()
