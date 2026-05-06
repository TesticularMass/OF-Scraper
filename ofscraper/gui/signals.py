"""Central event hub for cross-component communication in the GUI.

Replaces PyQt signals with a lightweight callback-based event system.
Thread-safe: callbacks are dispatched on the main (tkinter) thread via
root.after() when a tkinter root is available.
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("shared")

# Reference to the tkinter root window — set by app.py at launch time.
_tk_root = None


def set_tk_root(root):
    """Register the tkinter root for thread-safe callback dispatch."""
    global _tk_root
    _tk_root = root


class AppSignals:
    """Central signal hub for cross-component communication in the GUI.

    Each signal is a named event that can have multiple subscribers.
    Emitting a signal calls all connected callbacks with the provided args.
    When emitted from a background thread, callbacks are scheduled on the
    main thread via ``root.after(0, ...)``.
    """

    # All known signal names — declared here for documentation / IDE support.
    _SIGNAL_NAMES = [
        # Navigation
        "navigate_to_page",        # (page_name: str)
        "help_anchor_requested",   # (anchor: str)

        # Scraper workflow
        "action_selected",         # (actions: set)
        "models_selected",         # (models: list)
        "areas_selected",          # (areas: list)
        "scrape_paid_toggled",     # (enabled: bool)
        "scrape_labels_toggled",   # (enabled: bool)
        "advanced_scrape_configured",  # (options: dict)
        "discord_configured",      # (enabled: bool)

        # Data loading
        "data_loading_started",    # ()
        "data_loading_finished",   # (rows: list)
        "data_replace",            # (rows: list)
        "data_loading_error",      # (error_msg: str)

        # Table / Downloads
        "downloads_queued",        # (row_data_list: list)
        "download_cart_updated",   # (count: int)

        # Progress
        "progress_task_added",     # (task_id: str, total: int)
        "progress_task_updated",   # (task_id: str, current: int)
        "progress_task_removed",   # (task_id: str)
        "overall_progress_updated",  # (completed: int, total: int)
        "download_speed_updated",  # (bytes_per_sec: float)
        "total_bytes_updated",     # (total_bytes: int)

        # Cell updates
        "cell_update",             # (row_key: str, column_name: str, new_value: str)

        # Log
        "log_message",             # (level: str, message: str)

        # Scraping lifecycle
        "scraping_finished",       # ()
        "cancel_scrape_requested", # ()

        # Media type filter
        "mediatypes_configured",   # (types: list)

        # Date range filter
        "date_range_configured",   # (config: dict)

        # Daemon mode
        "daemon_configured",       # (enabled: bool, interval_min: float, notify: bool, sound: bool)
        "daemon_next_run",         # (countdown_text: str)
        "daemon_run_starting",     # (run_number: int)
        "daemon_stopped",          # ()
        "stop_daemon_requested",   # ()

        # Notifications
        "show_notification",       # (title: str, message: str)

        # Like/Unlike results
        "posts_liked_updated",     # (results: dict)

        # Status
        "status_message",          # (message: str)
        "error_occurred",          # (title: str, message: str)

        # Theme
        "theme_changed",           # (is_dark: bool)

        # Config
        "config_updated",          # ()
    ]

    def __init__(self):
        self._callbacks: Dict[str, List[Callable]] = {
            name: [] for name in self._SIGNAL_NAMES
        }
        self._lock = threading.Lock()

    def connect(self, signal_name: str, callback: Callable):
        """Subscribe *callback* to the named signal."""
        with self._lock:
            if signal_name not in self._callbacks:
                self._callbacks[signal_name] = []
            self._callbacks[signal_name].append(callback)

    def disconnect(self, signal_name: str, callback: Optional[Callable] = None):
        """Unsubscribe *callback* from the named signal.

        If *callback* is ``None``, all callbacks for the signal are removed.
        """
        with self._lock:
            if signal_name not in self._callbacks:
                return
            if callback is None:
                self._callbacks[signal_name].clear()
            else:
                try:
                    self._callbacks[signal_name].remove(callback)
                except ValueError:
                    pass

    def emit(self, signal_name: str, *args: Any):
        """Emit the named signal, calling all connected callbacks with *args*.

        If called from a background thread and a tkinter root is available,
        callbacks are dispatched on the main thread.
        """
        with self._lock:
            cbs = list(self._callbacks.get(signal_name, []))

        if not cbs:
            return

        def _dispatch():
            for cb in cbs:
                try:
                    cb(*args)
                except Exception as e:
                    log.debug(f"[Signal] Error in callback for '{signal_name}': {e}")

        # If we're on the main thread or no root is set, call directly.
        # Otherwise schedule on the main thread.
        if _tk_root is not None and threading.current_thread() is not threading.main_thread():
            try:
                _tk_root.after(0, _dispatch)
            except Exception:
                # Root may have been destroyed; call directly as fallback.
                _dispatch()
        else:
            _dispatch()

    # ---- Convenience attribute-style access ----
    # Allows:  app_signals.action_selected.emit(actions)
    #          app_signals.action_selected.connect(callback)
    # This preserves the PyQt-style API that existing code uses.

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in _SIGNAL_NAMES:
            import logging as _logging
            _logging.getLogger("shared").debug(
                f"AppSignals: accessing unknown signal '{name}'"
            )
        return _SignalProxy(self, name)


class _SignalProxy:
    """Proxy object that provides .connect(), .disconnect(), .emit()
    for a named signal on an AppSignals instance."""

    __slots__ = ("_hub", "_name")

    def __init__(self, hub: AppSignals, name: str):
        object.__setattr__(self, "_hub", hub)
        object.__setattr__(self, "_name", name)

    def connect(self, callback: Callable):
        self._hub.connect(self._name, callback)

    def disconnect(self, callback: Optional[Callable] = None):
        self._hub.disconnect(self._name, callback)

    def emit(self, *args: Any):
        self._hub.emit(self._name, *args)


# Global signal instance
app_signals = AppSignals()
