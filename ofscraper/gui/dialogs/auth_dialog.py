import json
import logging
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import webbrowser
from typing import Optional

from ofscraper.gui.signals import app_signals
from ofscraper.gui.widgets.styled_button import StyledButton
import ofscraper.utils.paths.common as common_paths

log = logging.getLogger("shared")

AUTH_FIELDS = [
    ("sess", "Session Cookie (sess)"),
    ("auth_id", "Auth ID Cookie"),
    ("auth_uid", "Auth UID Cookie (optional, for 2FA)"),
    ("user_agent", "User Agent"),
    ("x-bc", "X-BC Header"),
]

BROWSERS = [
    "Chrome",
    "Chromium",
    "Firefox",
    "Opera",
    "Opera GX",
    "Edge",
    "Brave",
    "Vivaldi",
]


def _detect_user_agent(browser_name: str) -> str:
    """Try to detect the user agent string for the given browser.

    Checks the installed browser version and constructs a standard UA string.
    Returns empty string if detection fails.
    """
    import subprocess
    import shutil

    browser_name = browser_name.lower().replace(" ", "")
    os_name = platform.system()

    # Map browser names to executable names and version detection commands
    if os_name == "Windows":
        # On Windows, check registry or run the executable with --version
        version_commands = {
            "chrome": [
                r'reg query "HKLM\SOFTWARE\Google\Chrome\BLBeacon" /v version',
                r'reg query "HKLM\SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon" /v version',
            ],
            "chromium": [
                r'reg query "HKLM\SOFTWARE\Chromium\BLBeacon" /v version',
            ],
            "edge": [
                r'reg query "HKLM\SOFTWARE\Microsoft\Edge\BLBeacon" /v version',
                r'reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Edge\BLBeacon" /v version',
            ],
            "brave": [
                r'reg query "HKLM\SOFTWARE\BraveSoftware\Brave-Browser\BLBeacon" /v version',
                r'reg query "HKLM\SOFTWARE\WOW6432Node\BraveSoftware\Brave-Browser\BLBeacon" /v version',
            ],
            "vivaldi": [
                r'reg query "HKLM\SOFTWARE\Vivaldi\BLBeacon" /v version',
            ],
            "firefox": [
                r'reg query "HKLM\SOFTWARE\Mozilla\Mozilla Firefox" /v CurrentVersion',
                r'reg query "HKLM\SOFTWARE\WOW6432Node\Mozilla\Mozilla Firefox" /v CurrentVersion',
            ],
        }
    else:
        # Linux / macOS — use command-line --version
        version_commands = {
            "chrome": ["google-chrome --version", "google-chrome-stable --version"],
            "chromium": ["chromium --version", "chromium-browser --version"],
            "edge": ["microsoft-edge --version", "microsoft-edge-stable --version"],
            "brave": ["brave-browser --version", "brave --version"],
            "vivaldi": ["vivaldi --version", "vivaldi-stable --version"],
            "firefox": ["firefox --version"],
            "opera": ["opera --version"],
            "operagx": ["opera --version"],
        }

    # Try to get the version
    version = ""
    for cmd in version_commands.get(browser_name, []):
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=5
            )
            output = result.stdout.strip()
            if output:
                # Extract version number (e.g., "120.0.6099.130")
                import re
                match = re.search(r"(\d+\.\d+[\.\d]*)", output)
                if match:
                    version = match.group(1)
                    break
        except Exception:
            continue

    if not version:
        return ""

    # Build the OS part of the UA
    if os_name == "Windows":
        os_ua = "Windows NT 10.0; Win64; x64"
    elif os_name == "Darwin":
        mac_ver = platform.mac_ver()[0] or "10_15_7"
        mac_ver = mac_ver.replace(".", "_")
        os_ua = f"Macintosh; Intel Mac OS X {mac_ver}"
    else:
        os_ua = "X11; Linux x86_64"

    # Build browser-specific UA string
    if browser_name == "firefox":
        major = version.split(".")[0]
        return f"Mozilla/5.0 ({os_ua}; rv:{major}.0) Gecko/20100101 Firefox/{major}.0"
    else:
        # Chrome-based browsers all use the Chrome UA format
        return (
            f"Mozilla/5.0 ({os_ua}) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{version} Safari/537.36"
        )


def _find_firefox_cookie_file() -> Optional[str]:
    """Search all known Firefox profile locations for cookies.sqlite.

    Checks XDG, standard, Snap, and Flatpak install paths on Linux.
    Uses glob to find cookies.sqlite directly (more robust than parsing profiles.ini).
    Returns the path to cookies.sqlite if found, else None.
    """
    from pathlib import Path

    home = Path.home()
    candidates = [
        home / ".config" / "mozilla" / "firefox",           # XDG (KDE Neon, etc.)
        home / "snap" / "firefox" / "common" / ".mozilla" / "firefox",  # Snap
        home / ".mozilla" / "firefox",                       # Standard
        home / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",  # Flatpak
        home / ".mozilla" / "firefox-esr",                   # ESR
    ]

    for profile_dir in candidates:
        if not profile_dir.is_dir():
            continue
        # Glob for cookies.sqlite in any profile subdirectory
        cookie_files = sorted(
            profile_dir.glob("*/cookies.sqlite"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,  # most recently modified first
        )
        if cookie_files:
            log.debug(f"Found Firefox cookies: {cookie_files[0]}")
            return str(cookie_files[0])

    return None


class AuthPage(ttk.Frame):
    """Authentication credential editor page -- replaces the InquirerPy auth prompt.
    Displayed inline as a page in the main window stack."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._inputs = {}       # field_key -> tk.StringVar
        self._entries = {}      # field_key -> ttk.Entry (needed for sess show/hide)
        self._sess_visible = False
        self._setup_ui()
        self._load_auth()

    def _setup_ui(self):
        # Outer padding
        outer = ttk.Frame(self, padding=(40, 40, 40, 40))
        outer.pack(fill="both", expand=True)

        # Header
        header = ttk.Label(outer, text="Authentication", style="Heading.TLabel")
        header.pack(anchor="w", pady=(0, 4))

        subtitle = ttk.Label(
            outer,
            text=(
                "Enter your OnlyFans authentication credentials. "
                "These are stored in auth.json in your profile directory."
            ),
            style="Subheading.TLabel",
            wraplength=700,
        )
        subtitle.pack(anchor="w", pady=(0, 16))

        # --- Credentials group ---
        form_group = ttk.LabelFrame(outer, text="Credentials", padding=(12, 12))
        form_group.pack(fill="x", pady=(0, 12))
        form_group.columnconfigure(1, weight=1)

        for i, (field_key, label_text) in enumerate(AUTH_FIELDS):
            ttk.Label(form_group, text=label_text + ":").grid(
                row=i, column=0, sticky="w", padx=(8, 4), pady=4
            )
            var = tk.StringVar()
            entry = ttk.Entry(form_group, textvariable=var, width=50)
            entry.grid(row=i, column=1, sticky="ew", padx=(4, 4), pady=4)
            self._inputs[field_key] = var
            self._entries[field_key] = entry

            if field_key == "sess":
                # Password toggle button next to sess entry
                entry.configure(show="*")
                toggle_btn = ttk.Button(
                    form_group, text="Show", width=6,
                    command=self._toggle_sess_visibility,
                )
                toggle_btn.grid(row=i, column=2, padx=(2, 8), pady=4)
                self._sess_toggle_btn = toggle_btn

        # --- Import from browser group ---
        import_group = ttk.LabelFrame(
            outer, text="Import from Browser *", padding=(12, 12)
        )
        import_group.pack(fill="x", pady=(0, 12))

        info_label = ttk.Label(
            import_group,
            text=(
                "* This feature is a work in progress and may not work on all systems.\n"
                "Imports cookies (sess, auth_id) and detects User Agent automatically.\n"
                "X-BC Header must still be entered manually from browser DevTools "
                "(F12 > Network tab).\n"
                "Only works with the browser's default profile. "
                "The browser must be closed before importing."
            ),
            style="Muted.TLabel",
            wraplength=700,
            justify="left",
        )
        info_label.pack(anchor="w", pady=(0, 8))

        import_row = ttk.Frame(import_group)
        import_row.pack(anchor="w")

        ttk.Label(import_row, text="Browser:").pack(side="left", padx=(0, 4))

        self._browser_var = tk.StringVar(value=BROWSERS[0])
        self.browser_combo = ttk.Combobox(
            import_row,
            textvariable=self._browser_var,
            values=BROWSERS,
            state="readonly",
            width=16,
        )
        self.browser_combo.pack(side="left", padx=(0, 8))

        import_btn = StyledButton(
            import_row, text="Import Cookies", command=self._import_from_browser
        )
        import_btn.pack(side="left")

        # --- Troubleshooting help group ---
        help_group = ttk.LabelFrame(
            outer, text="Still having issues?", padding=(12, 12)
        )
        help_group.pack(fill="x", pady=(0, 12))

        help_label = ttk.Label(
            help_group,
            text=(
                "If authentication keeps failing, try the following:\n"
                "\n"
                "1. Make sure you are logged into OnlyFans in your browser\n"
                "2. Try changing the Dynamic Rules setting in Configuration > General\n"
                "    (try 'digitalcriminals', 'datawhores', or 'xagler')\n"
                "3. Clear your browser cookies for OnlyFans, log in again, and re-import\n"
                "4. Manually copy all values from browser DevTools "
                "(F12 > Network tab > any API request headers)\n"
                "5. Check the OF-Scraper docs:"
            ),
            style="Muted.TLabel",
            wraplength=700,
            justify="left",
        )
        help_label.pack(anchor="w", pady=(0, 8))

        docs_btn = StyledButton(
            help_group,
            text="Open Auth Help Docs",
            command=lambda: webbrowser.open(
                "https://of-scraper.gitbook.io/of-scraper/auth"
            ),
        )
        docs_btn.pack(anchor="w")

        # --- Spacer (pushes action buttons to bottom) ---
        spacer = ttk.Frame(outer)
        spacer.pack(fill="both", expand=True)

        # --- Action buttons ---
        btn_frame = ttk.Frame(outer)
        btn_frame.pack(fill="x", pady=(12, 0))

        save_btn = StyledButton(
            btn_frame, text="Save", primary=True, command=self._save_auth, width=14
        )
        save_btn.pack(side="right", padx=(8, 0))

        reload_btn = StyledButton(
            btn_frame, text="Reload", command=self._load_auth
        )
        reload_btn.pack(side="right", padx=(8, 0))

        open_auth_btn = StyledButton(
            btn_frame, text="Open auth.json", command=self._open_auth_file
        )
        open_auth_btn.pack(side="right")

    @staticmethod
    def _open_auth_file():
        """Open auth.json in the system default editor/viewer."""
        try:
            auth_path = str(common_paths.get_auth_file())
            if platform.system() == "Windows":
                os.startfile(auth_path)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.Popen(["open", auth_path])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", auth_path])
        except Exception as e:
            log.error(f"Failed to open auth.json: {e}")

    def _toggle_sess_visibility(self):
        """Toggle session cookie field between visible text and dots."""
        sess_entry = self._entries.get("sess")
        if not sess_entry:
            return
        if self._sess_visible:
            sess_entry.configure(show="*")
            self._sess_toggle_btn.configure(text="Show")
            self._sess_visible = False
        else:
            sess_entry.configure(show="")
            self._sess_toggle_btn.configure(text="Hide")
            self._sess_visible = True

    def _load_auth(self):
        """Load current auth.json values into the form."""
        try:
            from ofscraper.utils.auth.utils.dict import get_auth_dict, get_empty
            try:
                auth = get_auth_dict()
            except Exception:
                auth = get_empty()

            for field_key, _ in AUTH_FIELDS:
                value = auth.get(field_key, "")
                self._inputs[field_key].set(str(value) if value else "")

            # Mask session cookie after loading
            sess_entry = self._entries.get("sess")
            if sess_entry and self._inputs["sess"].get():
                sess_entry.configure(show="*")
                self._sess_visible = False
                if hasattr(self, "_sess_toggle_btn"):
                    self._sess_toggle_btn.configure(text="Show")

            app_signals.status_message.emit("Auth credentials loaded")
        except Exception as e:
            log.error(f"Failed to load auth: {e}")
            app_signals.status_message.emit(f"Failed to load auth: {e}")

    def _save_auth(self):
        """Save form values to auth.json."""
        try:
            auth = {}
            for field_key, _ in AUTH_FIELDS:
                auth[field_key] = self._inputs[field_key].get().strip()

            # Warn about missing required fields but still allow save
            required = ["sess", "auth_id", "user_agent", "x-bc"]
            missing = [k for k in required if not auth.get(k)]
            if missing:
                reply = messagebox.askyesno(
                    "Missing Fields",
                    f"The following required fields are empty: {', '.join(missing)}\n\n"
                    "Save anyway? (Auth may not work until all fields are filled.)",
                    default="no",
                )
                if not reply:
                    return

            from ofscraper.utils.auth.file import write_auth
            import ofscraper.utils.paths.common as common_paths
            auth_path = common_paths.get_auth_file()
            auth_path.parent.mkdir(parents=True, exist_ok=True)
            log.info(f"Saving auth to: {auth_path}")
            write_auth(json.dumps(auth))
            log.info(f"Auth saved successfully. Keys with values: {[k for k in required if auth.get(k)]}")

            # Mask session cookie after saving
            sess_entry = self._entries.get("sess")
            if sess_entry and self._inputs["sess"].get():
                sess_entry.configure(show="*")
                self._sess_visible = False
                if hasattr(self, "_sess_toggle_btn"):
                    self._sess_toggle_btn.configure(text="Show")

            app_signals.status_message.emit("Auth credentials saved")
            messagebox.showinfo("Saved", "Authentication credentials saved successfully.")
        except Exception as e:
            log.error(f"Failed to save auth: {e}")
            messagebox.showerror("Error", f"Failed to save: {e}")

    def _import_from_browser(self):
        """Attempt to import cookies and detect user agent from the selected browser."""
        browser_display = self._browser_var.get()
        browser_name = browser_display.lower().replace(" ", "")
        try:
            import browser_cookie3

            browser_func_map = {
                "chrome": browser_cookie3.chrome,
                "chromium": browser_cookie3.chromium,
                "firefox": browser_cookie3.firefox,
                "opera": browser_cookie3.opera,
                "operagx": browser_cookie3.opera_gx,
                "edge": browser_cookie3.edge,
                "brave": browser_cookie3.brave,
                "vivaldi": browser_cookie3.vivaldi,
            }

            func = browser_func_map.get(browser_name)
            if not func:
                messagebox.showwarning(
                    "Error", f"Unsupported browser: {browser_name}"
                )
                return

            # For Firefox on Linux, try to find the cookie file manually
            # since browser_cookie3 may miss Snap/Flatpak profile paths
            kwargs = {"domain_name": "onlyfans"}
            if browser_name == "firefox" and platform.system() == "Linux":
                cookie_path = _find_firefox_cookie_file()
                if cookie_path:
                    kwargs["cookie_file"] = cookie_path
                    log.debug(f"Using Firefox cookie file: {cookie_path}")

            cj = func(**kwargs)
            cookies = {c.name: c.value for c in cj}

            imported = []
            if "sess" in cookies:
                self._inputs["sess"].set(cookies["sess"])
                imported.append("sess")
            if "auth_id" in cookies:
                self._inputs["auth_id"].set(cookies["auth_id"])
                imported.append("auth_id")
            for name, val in cookies.items():
                if name.startswith("auth_uid_"):
                    self._inputs["auth_uid"].set(val)
                    imported.append("auth_uid")
                    break

            # Try to auto-detect user agent from installed browser version
            ua_detected = False
            if not self._inputs["user_agent"].get().strip():
                try:
                    ua = _detect_user_agent(browser_name)
                    if ua:
                        self._inputs["user_agent"].set(ua)
                        imported.append("user_agent")
                        ua_detected = True
                except Exception as e:
                    log.debug(f"User agent detection failed: {e}")

            if imported:
                app_signals.status_message.emit(
                    f"Imported {', '.join(imported)} from {browser_display}"
                )

                # Build result message
                msg_parts = [f"Imported: {', '.join(imported)}"]
                if ua_detected:
                    msg_parts.append(
                        "User Agent was auto-detected from your browser version. "
                        "Verify it matches what you see in browser DevTools."
                    )
                else:
                    msg_parts.append(
                        "User Agent could not be detected automatically. "
                        "Please enter it manually from browser DevTools (F12 > Network tab)."
                    )
                msg_parts.append(
                    "\nX-BC Header must be entered manually.\n"
                    "Open OnlyFans in your browser, press F12, go to Network tab,\n"
                    "click any API request, and copy the 'x-bc' value from Request Headers."
                )
                messagebox.showinfo(
                    "Import Results", "\n\n".join(msg_parts)
                )
            else:
                messagebox.showwarning(
                    "No Cookies Found",
                    f"No OnlyFans cookies found in {browser_display}.\n\n"
                    "Make sure you are logged into OnlyFans in that browser\n"
                    "and that the browser is closed before importing.\n\n"
                    "Note: Only the browser's default profile is supported.",
                )
        except Exception as e:
            log.error(f"Browser import failed: {e}")
            log.debug(traceback.format_exc())
            messagebox.showerror(
                "Import Failed",
                f"Could not import cookies from {browser_display}:\n{e}\n\n"
                "Make sure the browser is fully closed and try again.",
            )
