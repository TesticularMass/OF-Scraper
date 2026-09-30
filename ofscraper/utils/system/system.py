import re
import logging
import os
import platform
import sys

import psutil
from setproctitle import setproctitle


def set_terminal_blocking():
    """Repair terminal flags inherited from an earlier uvloop-based run."""
    if os.name != "posix":
        return
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            if stream.isatty():
                os.set_blocking(stream.fileno(), True)
        except (AttributeError, OSError, ValueError):
            # Captured or closed streams may not expose a usable descriptor.
            pass


def getcpu_count():
    if platform.system() != "Darwin":
        return len(psutil.Process().cpu_affinity())
    else:
        return psutil.cpu_count()


def get_dupe_ofscraper():
    log = logging.getLogger("shared")
    found = []
    for proc in psutil.process_iter():
        try:
            if (
                proc
                and proc.status() == "running"
                and proc.pid != os.getpid()
                and proc.name() == "OF-Scraper"
            ):
                found.append(proc)
        except psutil.NoSuchProcess:
            pass
    if found:
        log.debug(f"Duplicated Processes {found}")
    return found


def setName():
    log = logging.getLogger("shared")
    try:
        setproctitle("OF-Scraper")
    except Exception as E:
        log.debug(E)
