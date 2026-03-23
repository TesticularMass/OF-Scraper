import json
import logging
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
import webbrowser

from ofscraper.gui.signals import app_signals
from ofscraper.gui.widgets.styled_button import StyledButton
import ofscraper.utils.paths.common as common_paths

log = logging.getLogger("shared")


class ConfigPage(ttk.Frame):
    """Configuration editor page — replaces the InquirerPy config prompt.
    Uses a ttk.Notebook to organize settings by category."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._config = {}
        # Each entry: (widget_type, var, widget)
        # widget_type is "line", "spin", "check", "combo", "path"
        self._widgets = {}
        self._tab_index = {}
        self._tab_canvases = {}
        self._setup_ui()
        self._load_config()
        app_signals.theme_changed.connect(self._apply_theme)
        app_signals.config_updated.connect(self._load_config)

    def _apply_theme(self, _is_dark=True):
        # ttk handles theming; nothing to do here
        pass

    def _setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header
        header = ttk.Label(self, text="Configuration", font=("Segoe UI", 22, "bold"))
        header.grid(row=0, column=0, sticky=tk.W, padx=24, pady=(24, 4))

        subtitle = ttk.Label(
            self, text="Edit application settings. Changes are saved to config.json."
        )
        subtitle.grid(row=1, column=0, sticky=tk.W, padx=24, pady=(0, 12))

        # Tab widget (Notebook)
        self.tabs = ttk.Notebook(self)

        def _add_tab(widget, label):
            self.tabs.add(widget, text=label)
            idx = self.tabs.index("end") - 1
            self._tab_index[label] = idx
            return idx

        _add_tab(self._create_general_tab(), "General")
        _add_tab(self._create_file_tab(), "File Options")
        _add_tab(self._create_download_tab(), "Download")
        _add_tab(self._create_performance_tab(), "Performance")
        _add_tab(self._create_content_tab(), "Content")
        _add_tab(self._create_cdm_tab(), "CDM")
        _add_tab(self._create_advanced_tab(), "Advanced")
        _add_tab(self._create_response_tab(), "Response Type")

        self.tabs.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))

        # Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, sticky=tk.E, padx=24, pady=(0, 24))

        open_config_btn = StyledButton(
            btn_frame, text="Open config.json", command=self._open_config_file
        )
        open_config_btn.pack(side=tk.LEFT, padx=(0, 8))

        reload_btn = StyledButton(
            btn_frame, text="Reload", command=self._load_config
        )
        reload_btn.pack(side=tk.LEFT, padx=(0, 8))

        save_btn = StyledButton(
            btn_frame, text="Save", primary=True, command=self._save_config
        )
        save_btn.pack(side=tk.LEFT)

    def _open_config_file(self):
        path = str(common_paths.get_config_path())
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                webbrowser.open("file:///" + path)
        except Exception as e:
            log.error(f"Failed to open config file: {e}")

    def go_to_config_field(self, tab_label: str, key: Optional[str] = None):
        """Navigate to a specific tab and optionally focus a config widget by key."""
        try:
            idx = self._tab_index.get(tab_label)
            if idx is None:
                return
            self.tabs.select(idx)
            if not key:
                return
            entry = self._widgets.get(key)
            if not entry:
                return
            _widget_type, _var, widget = entry
            try:
                # Scroll the canvas to make the widget visible
                canvas = self._tab_canvases.get(tab_label)
                if canvas is not None:
                    self.update_idletasks()
                    widget.update_idletasks()
                    y = widget.winfo_y()
                    canvas.yview_moveto(0)
                    self.update_idletasks()
                    canvas_height = canvas.winfo_height()
                    scroll_region = canvas.bbox("all")
                    if scroll_region and canvas_height > 0:
                        total_height = scroll_region[3]
                        if total_height > canvas_height:
                            frac = max(0, (y - canvas_height // 3)) / total_height
                            canvas.yview_moveto(frac)
            except Exception:
                pass
            try:
                widget.focus_set()
            except Exception:
                pass
        except Exception:
            pass

    def _create_scrollable_form(self, tab_label=None):
        """Create a scrollable frame with an inner frame for form widgets."""
        frame = ttk.Frame(self.tabs)
        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_win = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_win, width=e.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling
        def _on_enter(e):
            canvas.bind_all(
                "<MouseWheel>",
                lambda ev: canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"),
            )

        def _on_leave(e):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)

        if tab_label:
            self._tab_canvases[tab_label] = canvas

        # Configure inner frame grid columns for form layout
        inner.columnconfigure(1, weight=1)

        return frame, inner

    def _next_row(self, inner):
        """Return the next available grid row in the inner frame."""
        return inner.grid_size()[1]

    def _add_line(self, inner, key, label, placeholder="", tooltip=""):
        row = self._next_row(inner)
        var = tk.StringVar()
        lbl = ttk.Label(inner, text=label + ":")
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(12, 8), pady=5)
        entry = ttk.Entry(inner, textvariable=var)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=(0, 12), pady=5)
        self._widgets[key] = ("line", var, entry)
        return var, entry

    def _add_spin(self, inner, key, label, min_val=0, max_val=9999, default=0, tooltip=""):
        row = self._next_row(inner)
        var = tk.IntVar(value=default)
        lbl = ttk.Label(inner, text=label + ":")
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(12, 8), pady=5)
        spin = ttk.Spinbox(inner, textvariable=var, from_=min_val, to=max_val, width=10)
        spin.grid(row=row, column=1, sticky=tk.W, padx=(0, 12), pady=5)
        self._widgets[key] = ("spin", var, spin)
        return var, spin

    def _add_check(self, inner, key, label, default=False, tooltip=""):
        row = self._next_row(inner)
        var = tk.BooleanVar(value=default)
        lbl = ttk.Label(inner, text=label + ":")
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(12, 8), pady=5)
        chk = ttk.Checkbutton(inner, variable=var)
        chk.grid(row=row, column=1, sticky=tk.W, padx=(0, 12), pady=5)
        self._widgets[key] = ("check", var, chk)
        return var, chk

    def _add_combo(self, inner, key, label, items, tooltip=""):
        row = self._next_row(inner)
        var = tk.StringVar()
        lbl = ttk.Label(inner, text=label + ":")
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(12, 8), pady=5)
        combo = ttk.Combobox(inner, textvariable=var, values=items, state="readonly")
        combo.grid(row=row, column=1, sticky=tk.EW, padx=(0, 12), pady=5)
        if items:
            var.set(items[0])
        self._widgets[key] = ("combo", var, combo)
        return var, combo

    def _add_path(self, inner, key, label, is_dir=True, tooltip=""):
        row = self._next_row(inner)
        var = tk.StringVar()
        lbl = ttk.Label(inner, text=label + ":")
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(12, 8), pady=5)
        path_frame = ttk.Frame(inner)
        path_frame.grid(row=row, column=1, sticky=tk.EW, padx=(0, 12), pady=5)
        path_frame.columnconfigure(0, weight=1)
        entry = ttk.Entry(path_frame, textvariable=var)
        entry.grid(row=0, column=0, sticky=tk.EW)
        browse_btn = StyledButton(
            path_frame,
            text="Browse",
            command=lambda: self._browse_path(var, is_dir),
        )
        browse_btn.grid(row=0, column=1, padx=(4, 0))
        self._widgets[key] = ("path", var, entry)
        return var, entry

    def _browse_path(self, var, is_dir):
        if is_dir:
            path = filedialog.askdirectory(title="Select Directory")
        else:
            path = filedialog.askopenfilename(title="Select File")
        if path:
            var.set(path)

    # ---- Tab Builders ----

    def _create_general_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="General")
        self._add_line(inner, "main_profile", "Main Profile", "main_profile")
        self._add_line(
            inner,
            "metadata",
            "Metadata Path",
            "{configpath}/{profile}/.data/{model_id}",
        )
        self._add_line(
            inner,
            "discord",
            "Discord Webhook URL",
            "https://discord.com/api/webhooks/...",
        )
        return frame

    def _create_file_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="File Options")
        self._add_path(inner, "save_location", "Save Location", is_dir=True)
        self._add_line(
            inner,
            "dir_format",
            "Directory Format",
            "{model_username}/{responsetype}/{mediatype}/",
        )
        self._add_line(
            inner, "file_format", "File Format", "{filename}.{ext}"
        )
        self._add_spin(inner, "textlength", "Text Length", 0, 999, 0)
        self._add_line(inner, "space_replacer", "Space Replacer", " ")
        self._add_line(inner, "date", "Date Format", "YYYY-MM-DD")
        self._add_combo(
            inner, "text_type_default", "Text Type", ["letter", "word"]
        )
        self._add_check(inner, "truncation_default", "Enable Truncation", True)
        return frame

    def _create_download_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="Download")
        self._add_spin(
            inner, "system_free_min", "Min Free Space (MB)", 0, 999999, 0
        )
        self._add_check(inner, "auto_resume", "Auto Resume", True)
        self._add_spin(
            inner, "max_post_count", "Max Post Count", 0, 999999, 0
        )
        self._add_path(inner, "ffmpeg", "FFmpeg Path", is_dir=False)
        self._add_check(
            inner, "verify_all_integrity", "Verify All Integrity", False
        )

        # Download filter (media types to include)
        row = self._next_row(inner)
        filter_lf = ttk.LabelFrame(
            inner, text="Download Filter (media types to include)"
        )
        filter_lf.grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, padx=12, pady=8
        )
        for i, mt in enumerate(["Images", "Audios", "Videos", "Text"]):
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(filter_lf, text=mt, variable=var)
            chk.pack(side=tk.LEFT, padx=8, pady=4)
            self._widgets[f"filter_{mt.lower()}"] = ("check", var, chk)

        self._add_line(inner, "post_script", "Post Script", "")
        return frame

    def _create_performance_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="Performance")
        self._add_spin(
            inner, "download_sems", "Download Semaphores", 1, 15, 6
        )
        self._add_spin(
            inner, "download_limit", "Download Speed Limit (KB/s)", 0, 999999, 0
        )
        return frame

    def _create_content_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="Content")
        self._add_check(inner, "block_ads", "Block Ads", False)
        self._add_line(inner, "file_size_max", "Max File Size", "0")
        self._add_line(inner, "file_size_min", "Min File Size", "0")
        self._add_spin(
            inner, "length_max", "Max Length (seconds)", 0, 999999, 0
        )
        self._add_spin(
            inner, "length_min", "Min Length (seconds)", 0, 999999, 0
        )
        return frame

    def _create_cdm_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="CDM")
        self._add_combo(
            inner,
            "key-mode-default",
            "Key Mode",
            ["cdrm", "cdrm2", "keydb", "manual"],
        )
        self._add_path(inner, "client-id", "Client ID File", is_dir=False)
        self._add_path(inner, "private-key", "Private Key File", is_dir=False)
        return frame

    def _create_advanced_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="Advanced")
        self._add_combo(
            inner,
            "dynamic-mode-default",
            "Dynamic Mode",
            [
                "datawhores",
                "digitalcriminals",
                "xagler",
                "rafa",
                "generic",
                "manual",
            ],
        )
        self._add_combo(
            inner,
            "cache-mode",
            "Cache Mode",
            ["sqlite", "json", "disabled"],
        )
        self._add_check(inner, "downloadbars", "Download Bars", True)
        self._add_check(inner, "sanitize_text", "Sanitize Text", False)
        self._add_combo(
            inner,
            "remove_hash_match",
            "Hash / duplicate handling",
            [
                "Don't hash files (fastest)",
                "Hash files only (no deletion)",
                "Hash + remove duplicates (deletes extra copies)",
            ],
        )
        self._add_check(
            inner, "incremental_downloads", "Incremental Downloads", False
        )
        self._add_path(inner, "temp_dir", "Temp Directory", is_dir=True)
        self._add_check(
            inner,
            "infinite_loop_action_mode",
            "Infinite Loop (Action Mode)",
            False,
        )
        self._add_line(
            inner, "default_user_list", "Default User List", "main"
        )
        self._add_line(inner, "default_black_list", "Default Black List", "")
        self._add_check(
            inner,
            "skip_unavailable_content",
            "Skip Unavailable Content",
            False,
        )
        self._add_combo(
            inner,
            "ssl_verify",
            "SSL Verify",
            ["custom", "true", "false"],
        )
        self._add_line(inner, "env_files", "Env Files", "")
        return frame

    def _create_response_tab(self):
        frame, inner = self._create_scrollable_form(tab_label="Response Type")
        resp_types = [
            "timeline",
            "message",
            "archived",
            "paid",
            "stories",
            "highlights",
            "profile",
            "pinned",
            "streams",
        ]
        for rt in resp_types:
            self._add_line(inner, f"resp_{rt}", rt.capitalize(), rt)
        return frame

    # ---- Load / Save ----

    def _load_config(self):
        """Load current config values into the widgets."""
        try:
            from ofscraper.utils.config.config import read_config

            self._config = read_config(update=False) or {}

            # Flatten nested config into widget values
            config = self._config
            flat = {}

            # Top-level
            for k in ["main_profile", "metadata", "discord"]:
                flat[k] = config.get(k, "")

            # Nested sections
            for section_key, fields in [
                (
                    "file_options",
                    [
                        "save_location",
                        "dir_format",
                        "file_format",
                        "textlength",
                        "space_replacer",
                        "date",
                        "text_type_default",
                        "truncation_default",
                    ],
                ),
                (
                    "download_options",
                    [
                        "system_free_min",
                        "auto_resume",
                        "max_post_count",
                        "verify_all_integrity",
                    ],
                ),
                ("binary_options", ["ffmpeg"]),
                ("scripts_options", ["post_script"]),
                ("performance_options", ["download_sems", "download_limit"]),
                (
                    "content_filter_options",
                    [
                        "block_ads",
                        "file_size_max",
                        "file_size_min",
                        "length_max",
                        "length_min",
                    ],
                ),
                (
                    "cdm_options",
                    ["key-mode-default", "client-id", "private-key"],
                ),
                (
                    "advanced_options",
                    [
                        "dynamic-mode-default",
                        "cache-mode",
                        "downloadbars",
                        "sanitize_text",
                        "remove_hash_match",
                        "incremental_downloads",
                        "temp_dir",
                        "infinite_loop_action_mode",
                        "default_user_list",
                        "default_black_list",
                        "skip_unavailable_content",
                        "ssl_verify",
                        "env_files",
                    ],
                ),
            ]:
                section = config.get(section_key, {})
                if isinstance(section, dict):
                    for f in fields:
                        flat[f] = section.get(f, "")

            # Response type
            resp = config.get("responsetype", {})
            if isinstance(resp, dict):
                for rt in resp:
                    flat[f"resp_{rt}"] = resp.get(rt, rt)

            # Apply to widgets
            for key, entry in self._widgets.items():
                widget_type, var, widget = entry
                val = flat.get(key, "")
                if widget_type in ("line", "path"):
                    # JSON fields: serialize dicts/lists as JSON for display
                    if (
                        key == "custom_values" or key.startswith("ow_")
                    ) and isinstance(val, (dict, list)):
                        var.set(json.dumps(val) if val else "")
                    else:
                        var.set(str(val) if val else "")
                elif widget_type == "spin":
                    try:
                        var.set(int(val) if val else 0)
                    except (ValueError, TypeError):
                        var.set(0)
                elif widget_type == "check":
                    # Some legacy configs stored strings; normalize known cases.
                    if key == "infinite_loop_action_mode" and isinstance(
                        val, str
                    ):
                        v = val.strip().lower()
                        if v in {
                            "disabled",
                            "false",
                            "0",
                            "no",
                            "off",
                            "",
                        }:
                            var.set(False)
                        elif v in {"after", "true", "1", "yes", "on"}:
                            var.set(True)
                        else:
                            var.set(bool(val))
                    else:
                        var.set(bool(val))
                elif widget_type == "combo":
                    str_val = str(val) if val else ""
                    combo_values = widget.cget("values")
                    if str_val in combo_values:
                        var.set(str_val)
                    else:
                        var.set(str_val)

            # Download filter checkboxes
            try:
                dl_filter = config.get("download_options", {}).get(
                    "filter", None
                )
                if dl_filter is None:
                    # Default: all checked
                    for mt in ["images", "audios", "videos", "text"]:
                        entry = self._widgets.get(f"filter_{mt}")
                        if entry:
                            _wt, var, _w = entry
                            var.set(True)
                else:
                    active = {s.lower() for s in dl_filter}
                    for mt in ["images", "audios", "videos", "text"]:
                        entry = self._widgets.get(f"filter_{mt}")
                        if entry:
                            _wt, var, _w = entry
                            var.set(mt in active)
            except Exception:
                pass

            # Normalize remove_hash_match tri-state into the UI choices.
            try:
                entry = self._widgets.get("remove_hash_match")
                if entry and entry[0] == "combo":
                    _wt, var, widget = entry
                    val = flat.get("remove_hash_match", "")
                    if val is None:
                        choice = "Don't hash files (fastest)"
                    elif isinstance(val, str):
                        val_lower = val.strip().lower()
                        if val_lower in ("true", "1", "yes"):
                            choice = (
                                "Hash + remove duplicates (deletes extra copies)"
                            )
                        else:
                            choice = "Hash files only (no deletion)"
                    elif bool(val):
                        choice = (
                            "Hash + remove duplicates (deletes extra copies)"
                        )
                    else:
                        choice = "Hash files only (no deletion)"
                    var.set(choice)
            except Exception:
                pass

            app_signals.status_message.emit("Configuration loaded")
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            app_signals.status_message.emit(f"Failed to load config: {e}")

    def _save_config(self):
        """Collect widget values and save to config.json."""
        try:
            config = dict(self._config) if self._config else {}

            # Helper to set nested dict values
            def set_nested(d, section, key, val):
                if section not in d:
                    d[section] = {}
                d[section][key] = val

            # Top-level
            for k in ["main_profile", "metadata", "discord"]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    config[k] = var.get()

            # File options
            for k in [
                "save_location",
                "dir_format",
                "file_format",
                "space_replacer",
                "date",
            ]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(config, "file_options", k, var.get())

            entry = self._widgets.get("textlength")
            if entry:
                _wt, var, _w = entry
                set_nested(config, "file_options", "textlength", var.get())
            entry = self._widgets.get("text_type_default")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "file_options", "text_type_default", var.get()
                )
            entry = self._widgets.get("truncation_default")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "file_options", "truncation_default", var.get()
                )

            # Download
            entry = self._widgets.get("system_free_min")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "download_options", "system_free_min", var.get()
                )
            entry = self._widgets.get("auto_resume")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "download_options", "auto_resume", var.get()
                )
            entry = self._widgets.get("max_post_count")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "download_options", "max_post_count", var.get()
                )
            entry = self._widgets.get("verify_all_integrity")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config,
                    "download_options",
                    "verify_all_integrity",
                    var.get(),
                )

            # Download filter
            active_filter = []
            for mt in ["Images", "Audios", "Videos", "Text"]:
                entry = self._widgets.get(f"filter_{mt.lower()}")
                if entry:
                    _wt, var, _w = entry
                    if var.get():
                        active_filter.append(mt)
            set_nested(config, "download_options", "filter", active_filter)

            # Binary
            entry = self._widgets.get("ffmpeg")
            if entry:
                _wt, var, _w = entry
                set_nested(config, "binary_options", "ffmpeg", var.get())

            # Scripts
            entry = self._widgets.get("post_script")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "scripts_options", "post_script", var.get()
                )

            # Performance
            for k in ["download_sems", "download_limit"]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(
                        config, "performance_options", k, var.get()
                    )

            # Content
            entry = self._widgets.get("block_ads")
            if entry:
                _wt, var, _w = entry
                set_nested(
                    config, "content_filter_options", "block_ads", var.get()
                )
            for k in ["file_size_max", "file_size_min"]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(
                        config, "content_filter_options", k, var.get()
                    )
            for k in ["length_max", "length_min"]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(
                        config, "content_filter_options", k, var.get()
                    )

            # CDM
            for k in ["key-mode-default", "client-id", "private-key"]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(config, "cdm_options", k, var.get())

            # Advanced
            for k in ["dynamic-mode-default", "cache-mode", "ssl_verify"]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(config, "advanced_options", k, var.get())

            # Tri-state-ish handling for remove_hash_match (None/False/True)
            entry = self._widgets.get("remove_hash_match")
            if entry and entry[0] == "combo":
                _wt, var, _w = entry
                txt = var.get()
                if txt.startswith("Don't hash"):
                    set_nested(
                        config, "advanced_options", "remove_hash_match", None
                    )
                elif txt.startswith("Hash + remove"):
                    set_nested(
                        config, "advanced_options", "remove_hash_match", True
                    )
                else:
                    set_nested(
                        config, "advanced_options", "remove_hash_match", False
                    )

            for k in [
                "downloadbars",
                "sanitize_text",
                "incremental_downloads",
                "infinite_loop_action_mode",
                "skip_unavailable_content",
            ]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(config, "advanced_options", k, var.get())
            for k in [
                "temp_dir",
                "default_user_list",
                "default_black_list",
            ]:
                entry = self._widgets.get(k)
                if entry:
                    _wt, var, _w = entry
                    set_nested(config, "advanced_options", k, var.get())

            # env_files: comma-separated string -> list
            entry = self._widgets.get("env_files")
            if entry:
                _wt, var, _w = entry
                raw = var.get().strip()
                env_list = (
                    [s.strip() for s in raw.split(",") if s.strip()]
                    if raw
                    else []
                )
                set_nested(
                    config, "advanced_options", "env_files", env_list
                )

            # Response type
            resp = {}
            resp_types = [
                "timeline",
                "message",
                "archived",
                "paid",
                "stories",
                "highlights",
                "profile",
                "pinned",
                "streams",
            ]
            for rt in resp_types:
                entry = self._widgets.get(f"resp_{rt}")
                if entry:
                    _wt, var, _w = entry
                    resp[rt] = var.get() or rt
            config["responsetype"] = resp

            # Write config
            from ofscraper.utils.config.file import write_config

            write_config(config)

            # Invalidate the in-memory auth cache so a changed dynamic-mode-default
            # takes effect immediately without requiring a GUI restart.
            try:
                from ofscraper.utils.auth.request import invalidate_auth_cache

                invalidate_auth_cache()
            except Exception:
                pass

            app_signals.status_message.emit("Configuration saved")
            messagebox.showinfo("Saved", "Configuration saved successfully.")
        except Exception as e:
            log.error(f"Failed to save config: {e}")
            messagebox.showerror(
                "Error", f"Failed to save config:\n{e}"
            )
