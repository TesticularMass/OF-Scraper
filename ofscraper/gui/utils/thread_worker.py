"""Background thread workers for the tkinter GUI.

Replaces PyQt's QRunnable / QThread with standard library threading.
Results and errors are dispatched to the main thread via the signal hub.
"""

import asyncio
import logging
import threading
import traceback

from ofscraper.gui.signals import app_signals

log = logging.getLogger("shared")


class WorkerSignals:
    """Callback container matching the old WorkerSignals(QObject) API.

    Instead of pyqtSignals, each signal is a simple callable attribute
    that can be set by the caller.
    """

    def __init__(self):
        self._started = None
        self._finished = None
        self._error = None
        self._progress = None

    # ---- connect / emit helpers ----

    @property
    def started(self):
        return _SignalSlot(self, "_started")

    @property
    def finished(self):
        return _SignalSlot(self, "_finished")

    @property
    def error(self):
        return _SignalSlot(self, "_error")

    @property
    def progress(self):
        return _SignalSlot(self, "_progress")


class _SignalSlot:
    """Minimal proxy that supports .connect(cb) and .emit(*args)."""

    def __init__(self, owner, attr_name):
        self._owner = owner
        self._attr = attr_name
        self._callbacks = []

    def connect(self, cb):
        self._callbacks.append(cb)

    def emit(self, *args):
        from ofscraper.gui.signals import _tk_root
        def _dispatch():
            for cb in self._callbacks:
                try:
                    cb(*args)
                except Exception as e:
                    log.debug(f"[WorkerSignal] callback error: {e}")
        if _tk_root is not None and threading.current_thread() is not threading.main_thread():
            try:
                _tk_root.after(0, _dispatch)
            except Exception:
                _dispatch()
        else:
            _dispatch()


class Worker:
    """Generic worker for running functions in a background thread.

    Usage::

        w = Worker(some_function, arg1, arg2)
        w.signals.finished.connect(on_done)
        w.signals.error.connect(on_error)
        w.start()
    """

    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._thread = None

    def start(self):
        """Start the worker in a daemon thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self.signals.started.emit()
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            log.debug(traceback.format_exc())
            self.signals.error.emit(str(e))


class AsyncWorker:
    """Worker for running async coroutines in a background thread."""

    def __init__(self, coro_fn, *args, **kwargs):
        self.coro_fn = coro_fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self.signals.started.emit()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.coro_fn(*self.args, **self.kwargs)
                )
                self.signals.finished.emit(result)
            finally:
                loop.close()
        except Exception as e:
            log.debug(traceback.format_exc())
            self.signals.error.emit(str(e))


class LongRunningWorker:
    """Thread-based worker for long-running operations."""

    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._result = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self.signals.started.emit()
        try:
            self._result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(self._result)
        except Exception as e:
            log.debug(traceback.format_exc())
            self.signals.error.emit(str(e))

    def wait(self, timeout=None):
        """Wait for the worker thread to finish."""
        if self._thread:
            self._thread.join(timeout=timeout)

    @property
    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()
