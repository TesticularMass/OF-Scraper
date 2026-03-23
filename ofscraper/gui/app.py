"""Launch the tkinter GUI application.

This is the main entry point for the GUI — called from managers/manager.py.
"""

import logging
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from ofscraper.gui.signals import app_signals, set_tk_root
from ofscraper.gui.styles import apply_theme, set_theme
from ofscraper.gui.utils.progress_bridge import GUILogHandler

log = logging.getLogger("shared")


def _show_windows_toast(title: str, message: str) -> bool:
    """Show a native Windows 10/11 toast notification via PowerShell.

    Uses the Windows Runtime ToastNotificationManager API which appears in
    the Windows Notification Center.  Runs PowerShell in a hidden window.

    Returns True if the subprocess launched without error.
    """
    if sys.platform != "win32":
        return False
    try:
        ps_script = r"""
$RegPath = "HKCU:\SOFTWARE\Classes\AppUserModelId\OF-Scraper"
if (-not (Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
    New-ItemProperty -Path $RegPath -Name "DisplayName" -Value "OF-Scraper" -PropertyType String -Force | Out-Null
}

$t = [System.Security.SecurityElement]::Escape($env:TOAST_TITLE)
$m = [System.Security.SecurityElement]::Escape($env:TOAST_MSG)

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml("<toast><visual><binding template=`"ToastText02`"><text id=`"1`">$t</text><text id=`"2`">$m</text></binding></visual></toast>")

$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("OF-Scraper").Show($toast)
"""
        env = os.environ.copy()
        env["TOAST_TITLE"] = str(title)
        env["TOAST_MSG"] = str(message)
        proc = subprocess.Popen(
            [
                "powershell",
                "-WindowStyle", "Hidden",
                "-NonInteractive",
                "-Command", ps_script,
            ],
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        import threading

        def _log_stderr():
            try:
                _, stderr_data = proc.communicate(timeout=10)
                if proc.returncode != 0 and stderr_data:
                    log.debug(
                        f"[Toast] PowerShell error (rc={proc.returncode}): "
                        f"{stderr_data.decode(errors='replace').strip()}"
                    )
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception as exc:
                log.debug(f"[Toast] stderr reader error: {exc}")

        threading.Thread(target=_log_stderr, daemon=True).start()
        return True
    except Exception as e:
        log.debug(f"[Toast] Failed to launch PowerShell: {e}")
        return False


def launch_gui(manager=None):
    """Launch the tkinter GUI application."""
    root = tk.Tk()
    root.title("OF-Scraper")
    root.minsize(1200, 750)
    root.geometry("1400x850")

    # Register root for thread-safe signal dispatch
    set_tk_root(root)

    # Apply saved theme preference (falls back to dark if not set)
    try:
        from ofscraper.gui.utils.gui_settings import load_gui_settings
        _saved_theme = load_gui_settings().get("theme", "dark")
    except Exception:
        _saved_theme = "dark"
    set_theme(_saved_theme == "dark")
    apply_theme(root)

    # Attach GUI log handler to forward logs to the console widget
    gui_handler = GUILogHandler()
    gui_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    )
    for logger_name in ["shared", "shared_other"]:
        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(gui_handler)

    # Ensure auth.json exists (fresh installs won't have one yet)
    try:
        import json
        import ofscraper.utils.paths.common as common_paths
        import ofscraper.utils.auth.utils.dict as auth_dict

        auth_file = common_paths.get_auth_file()
        auth_file.parent.mkdir(parents=True, exist_ok=True)
        if not auth_file.exists():
            with open(auth_file, "w") as f:
                f.write(json.dumps(auth_dict.get_empty(), indent=4))
            log.info(f"Created empty auth.json at {auth_file}")
    except Exception as e:
        log.warning(f"Could not create auth.json: {e}")

    # Set up notification handler
    def _on_show_notification(title, message):
        if not _show_windows_toast(title, message):
            # Fallback: just log it
            log.info(f"[Notification] {title}: {message}")

    app_signals.show_notification.connect(_on_show_notification)

    # Create main window
    from ofscraper.gui.main_window import MainWindow
    window = MainWindow(root, manager=manager)
    window.pack(fill=tk.BOTH, expand=True)

    log.info("OF-Scraper GUI started")
    root.mainloop()
