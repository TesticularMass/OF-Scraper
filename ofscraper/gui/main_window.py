import logging
import tkinter as tk
from tkinter import ttk, messagebox

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import (
    apply_theme,
    set_theme,
    c,
    DARK_SIDEBAR_BG,
    LIGHT_SIDEBAR_BG,
    DARK_SEP_COLOR,
    LIGHT_SEP_COLOR,
    DARK_LOGO_COLOR,
    LIGHT_LOGO_COLOR,
)
from ofscraper.gui.utils.workflow import GUIWorkflow
from ofscraper.gui.widgets.styled_button import NavButton

log = logging.getLogger("shared")


class _PageStack(ttk.Frame):
    """Container that manages overlapping pages via place geometry.

    Pages are stacked on top of each other; _show_page() brings one to the front.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._pages = {}     # index -> frame
        self._current_idx = None

    def add_page(self, index, frame):
        self._pages[index] = frame
        frame.place(in_=self, x=0, y=0, relwidth=1, relheight=1)

    def _show_page(self, index):
        if index in self._pages:
            self._pages[index].tkraise()
            self._current_idx = index

    def count(self):
        return len(self._pages)


class MainWindow(ttk.Frame):
    """Central application frame with navigation sidebar and stacked pages."""

    def __init__(self, parent, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._root = parent
        self.manager = manager

        self._pages = {}
        self._nav_buttons = {}

        # Load saved theme preference (dark by default)
        try:
            from ofscraper.gui.utils.gui_settings import load_gui_settings
            _saved = load_gui_settings()
            self._is_dark = _saved.get("theme", "dark") == "dark"
            self._verbose_log = bool(_saved.get("verbose_log", False))
        except Exception:
            self._is_dark = True
            self._verbose_log = False
        set_theme(self._is_dark)
        if self._verbose_log:
            self._apply_verbose_log(True)

        # Initialize the workflow runner that bridges GUI -> scraper backend
        self.workflow = GUIWorkflow(manager)

        self._setup_ui()
        if not self._is_dark:
            self._apply_theme_visuals(emit_signal=False)
        if self._verbose_log:
            self._verbose_btn.configure(text="Verbose Log: On")
        self._connect_signals()
        self._navigate("scraper")
        # Deferred startup tasks
        self.after(250, self._maybe_show_missing_dependency_notice)
        self.after(350, self._maybe_autostart_from_cli_args)

    def _maybe_autostart_from_cli_args(self):
        """If invoked with --gui and sufficient CLI args, skip the GUI wizard."""
        try:
            import ofscraper.utils.args.accessors.read as read_args
            import ofscraper.utils.args.accessors.areas as areas_accessor
        except Exception:
            return

        try:
            args = read_args.retriveArgs()
        except Exception:
            return

        if not bool(getattr(args, "gui", False)):
            return

        raw_actions = getattr(args, "action", None) or []
        raw_users = getattr(args, "usernames", None) or []
        raw_posts = getattr(args, "posts", None) or []
        raw_da = getattr(args, "download_area", None) or []
        raw_la = getattr(args, "like_area", None) or []

        def _flatten_strs(v):
            out = []
            if v is None:
                return out
            if isinstance(v, (str, bytes)):
                return [str(v)]
            try:
                for item in v:
                    if isinstance(item, (list, set, tuple)):
                        out.extend([str(x) for x in item])
                    else:
                        out.append(str(item))
            except Exception:
                out.append(str(v))
            return out

        actions = {a.strip().lower() for a in _flatten_strs(raw_actions) if str(a).strip()}
        usernames = {u.strip().lower() for u in _flatten_strs(raw_users) if str(u).strip()}
        has_areas = bool(_flatten_strs(raw_posts) or _flatten_strs(raw_da) or _flatten_strs(raw_la))

        if not actions or not usernames or not has_areas:
            return

        log.info(
            f"[GUI] Auto-start detected from CLI args: actions={sorted(actions)}, "
            f"usernames={('ALL' if 'all' in usernames else sorted(usernames))}"
        )

        try:
            final_areas = set(areas_accessor.get_final_posts_area() or set())
        except Exception:
            final_areas = set()

        if "Label" in final_areas and "Labels" not in final_areas:
            final_areas.discard("Label")
            final_areas.add("Labels")

        # Configure the Area Selector page state
        try:
            self._navigate("scraper")
            self.scraper_stack._show_page(2)  # area page
        except Exception:
            pass

        try:
            self.area_page._scrape_paid_var.set(
                bool(getattr(args, "scrape_paid", False))
            )
        except Exception:
            pass

        try:
            if final_areas:
                for area, (cb, var) in getattr(self.area_page, "_area_checks", {}).items():
                    var.set(area in final_areas)
        except Exception:
            pass

        # Daemon (minutes)
        try:
            daemon_val = getattr(args, "daemon", None)
            if daemon_val is not None and float(daemon_val) > 0:
                self.area_page._daemon_var.set(True)
                self.area_page._daemon_interval_var.set(float(daemon_val))
            else:
                self.area_page._daemon_var.set(False)
        except Exception:
            pass

        # Load models in the background, then auto-select, then start scraping
        from ofscraper.gui.utils.thread_worker import Worker

        if not (self.manager and getattr(self.manager, "model_manager", None)):
            return

        def _fetch_models():
            self.manager.model_manager.all_subs_retriver()
            return getattr(self.manager.model_manager, "all_subs_obj", None) or []

        def _on_models(models):
            try:
                models = list(models or [])
                if not models:
                    return
                excluded = set()
                try:
                    excluded = {
                        str(x).strip().lower()
                        for x in (getattr(args, "excluded_username", None) or [])
                        if str(x).strip()
                    }
                except Exception:
                    excluded = set()

                if "all" in usernames:
                    selected_models = [
                        m for m in models
                        if getattr(m, "name", "").strip().lower() not in excluded
                    ]
                else:
                    want = set(usernames)
                    selected_models = [
                        m for m in models
                        if getattr(m, "name", "").strip().lower() in want
                        and getattr(m, "name", "").strip().lower() not in excluded
                    ]
                if not selected_models:
                    log.warning("[GUI] Auto-start: no matching models found for usernames")
                    return

                try:
                    app_signals.action_selected.emit(set(actions))
                except Exception:
                    pass

                app_signals.models_selected.emit(selected_models)

                def _start():
                    try:
                        self.table_page._on_start_scraping()
                    except Exception:
                        pass
                self.after(0, _start)
            except Exception:
                return

        worker = Worker(_fetch_models)
        worker.signals.finished.connect(_on_models)
        worker.start()

    def _setup_ui(self):
        self.columnconfigure(1, weight=1)  # content gets the stretch
        self.rowconfigure(0, weight=1)     # main row stretches

        # -- Left navigation sidebar --
        nav_frame = tk.Frame(self, width=190, bg=DARK_SIDEBAR_BG)
        nav_frame.grid(row=0, column=0, sticky="ns")
        nav_frame.grid_propagate(False)
        self._nav_frame = nav_frame

        # Logo (ASCII art)
        _logo_lines = [
            r"        __                                    ",
            r"  ___  / _|___  ___ _ __ __ _ _ __   ___ _ __ ",
            r" / _ \| |_/ __|/ __| '__/ _` | '_ \ / _ \ '__|",
            r"| (_) |  _\__ \ (__| | | (_| | |_) |  __/ |   ",
            r" \___/|_|_|___/\___|_|  \__,_| .__/ \___|_|   ",
            r"       / /     \ \      / /  |_|\ \           ",
            r"      | |       | |    | |       | |          ",
            r"      | |   _   | |    | |   _   | |          ",
            r"      | |  (_)  | |    | |  (_)  | |          ",
            r"       \_\     /_/      \_\     /_/           ",
        ]
        logo_text = "\n".join(_logo_lines)
        self._title_label = tk.Label(
            nav_frame, text=logo_text,
            font=("Consolas", 5), fg=DARK_LOGO_COLOR, bg=DARK_SIDEBAR_BG,
            justify=tk.CENTER,
        )
        self._title_label.pack(pady=(4, 12))

        # Separator
        self._nav_sep = tk.Frame(nav_frame, height=1, bg=DARK_SEP_COLOR)
        self._nav_sep.pack(fill=tk.X, padx=4, pady=4)

        # Nav buttons
        nav_items = [
            ("scraper", "Scraper"),
            ("auth", "Authentication"),
            ("config", "Configuration"),
            ("drm", "DRM Key Creation"),
            ("profiles", "Profiles"),
            ("merge", "Merge DBs"),
            ("help", "Help / README"),
        ]

        for page_id, label in nav_items:
            btn = NavButton(nav_frame, text=label,
                            command=lambda pid=page_id: self._navigate(pid))
            btn.pack(fill=tk.X, padx=8, pady=2)
            self._nav_buttons[page_id] = btn

        # Spacer
        spacer = tk.Frame(nav_frame, bg=DARK_SIDEBAR_BG)
        spacer.pack(fill=tk.BOTH, expand=True)
        self._nav_spacer = spacer

        # Theme toggle button
        self._theme_btn = ttk.Button(nav_frame, text="Light Mode",
                                      command=self._toggle_theme)
        self._theme_btn.pack(fill=tk.X, padx=8, pady=2)

        # Verbose log toggle button
        self._verbose_btn = ttk.Button(nav_frame, text="Verbose Log: Off",
                                        command=self._toggle_verbose_log)
        self._verbose_btn.pack(fill=tk.X, padx=8, pady=2)

        # Version label
        try:
            from ofscraper.__version__ import __version__
            ver_text = f"v{__version__}"
        except Exception:
            ver_text = "v3.12.9"
        self._ver_label = tk.Label(nav_frame, text=ver_text,
                                    font=("Segoe UI", 9),
                                    fg=c("muted"), bg=DARK_SIDEBAR_BG)
        self._ver_label.pack(pady=(4, 8))

        # -- Right content area (stacked pages) --
        self.stack = _PageStack(self)
        self.stack.grid(row=0, column=1, sticky="nsew")

        # Create pages
        self._create_pages()

        # Status bar
        self._status_label = ttk.Label(self, text="Ready", style="Muted.TLabel")
        self._status_label.grid(row=1, column=0, columnspan=2, sticky="ew",
                                 padx=12, pady=4)

    def _toggle_theme(self):
        """Switch between dark and light themes, then offer to save."""
        self._is_dark = not self._is_dark
        set_theme(self._is_dark)
        apply_theme(self._root)
        self._apply_theme_visuals()
        self._prompt_save_theme()

    def _toggle_verbose_log(self):
        """Toggle verbose (DEBUG-level) logging."""
        self._verbose_log = not self._verbose_log
        self._apply_verbose_log(self._verbose_log)
        try:
            from ofscraper.gui.utils.gui_settings import load_gui_settings, save_gui_settings
            s = load_gui_settings()
            s["verbose_log"] = self._verbose_log
            save_gui_settings(s)
        except Exception:
            pass
        state = "On" if self._verbose_log else "Off"
        app_signals.status_message.emit(f"Verbose logging {state}")

    def _apply_verbose_log(self, enable):
        """Toggle verbose (DEBUG) logging on or off."""
        import logging as _logging
        logger = _logging.getLogger("shared")

        _GUI_VERBOSE_TAG = "_gui_verbose_handler"

        if enable:
            logger.setLevel(_logging.DEBUG)
            for h in logger.handlers:
                if h.level > _logging.DEBUG or h.level == _logging.NOTSET:
                    h._gui_prev_level = h.level
                    h.setLevel(_logging.DEBUG)

            if not any(getattr(h, _GUI_VERBOSE_TAG, False) for h in logger.handlers):
                try:
                    import datetime as _dt
                    import ofscraper.utils.paths.common as _paths
                    import ofscraper.utils.config.data as _data

                    log_folder = _paths.get_log_folder()
                    profile = _data.get_main_profile()
                    timestamp = _dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
                    log_dir = log_folder / f"{profile}_{_dt.date.today().strftime('%Y-%m-%d')}"
                    log_dir.mkdir(parents=True, exist_ok=True)
                    log_path = log_dir / f"ofscraper_gui_verbose_{profile}_{timestamp}.log"

                    fmt = r" %(asctime)s:[%(module)s.%(funcName)s:%(lineno)d]  %(message)s"
                    stream = open(log_path, "a", encoding="utf-8")
                    fh = _logging.StreamHandler(stream)
                    fh.setLevel(_logging.DEBUG)
                    fh.setFormatter(_logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S"))
                    setattr(fh, _GUI_VERBOSE_TAG, True)
                    fh._gui_verbose_stream = stream
                    logger.addHandler(fh)
                    log.info(f"[GUI] Verbose log file: {log_path}")
                except Exception as e:
                    log.debug(f"[GUI] Could not create verbose log file: {e}")
        else:
            logger.setLevel(_logging.INFO)
            for h in logger.handlers:
                prev = getattr(h, "_gui_prev_level", _logging.INFO)
                h.setLevel(prev)

            for h in logger.handlers[:]:
                if getattr(h, _GUI_VERBOSE_TAG, False):
                    logger.removeHandler(h)
                    try:
                        stream = getattr(h, "_gui_verbose_stream", None)
                        h.close()
                        if stream:
                            stream.close()
                    except Exception:
                        pass

        try:
            self._verbose_btn.configure(text=f"Verbose Log: {'On' if enable else 'Off'}")
        except Exception:
            pass

    def _apply_theme_visuals(self, emit_signal=True):
        """Apply all visual elements for the current theme."""
        if self._is_dark:
            self._theme_btn.configure(text="Light Mode")
            sidebar_bg = DARK_SIDEBAR_BG
            sep_color = DARK_SEP_COLOR
            logo_color = DARK_LOGO_COLOR
        else:
            self._theme_btn.configure(text="Dark Mode")
            sidebar_bg = LIGHT_SIDEBAR_BG
            sep_color = LIGHT_SEP_COLOR
            logo_color = LIGHT_LOGO_COLOR

        # Update sidebar and separator colors
        self._nav_frame.configure(bg=sidebar_bg)
        self._nav_sep.configure(bg=sep_color)
        self._title_label.configure(fg=logo_color, bg=sidebar_bg)
        self._ver_label.configure(fg=c("muted"), bg=sidebar_bg)
        self._nav_spacer.configure(bg=sidebar_bg)

        if emit_signal:
            app_signals.theme_changed.emit(self._is_dark)

    def _prompt_save_theme(self):
        """Ask the user if they want to save the current theme as default."""
        theme_name = "Dark" if self._is_dark else "Light"
        if messagebox.askyesno(
            "Save Theme Preference",
            f"Set {theme_name} Mode as your default theme?\n\n"
            f"The preference will be saved to gui_settings.json in your "
            f"ofscraper config directory.",
        ):
            try:
                from ofscraper.gui.utils.gui_settings import (
                    load_gui_settings,
                    save_gui_settings,
                )
                settings = load_gui_settings()
                settings["theme"] = "dark" if self._is_dark else "light"
                if save_gui_settings(settings):
                    log.info(
                        f"[GUI] Default theme saved: {'dark' if self._is_dark else 'light'}"
                    )
            except Exception as e:
                log.warning(f"[GUI] Could not save theme preference: {e}")

    def _create_pages(self):
        from ofscraper.gui.pages.action_page import ActionPage
        from ofscraper.gui.pages.model_selector_page import ModelSelectorPage
        from ofscraper.gui.pages.area_selector_page import AreaSelectorPage
        from ofscraper.gui.pages.table_page import TablePage
        from ofscraper.gui.pages.help_page import HelpPage
        from ofscraper.gui.dialogs.auth_dialog import AuthPage
        from ofscraper.gui.dialogs.config_dialog import ConfigPage
        from ofscraper.gui.dialogs.profile_dialog import ProfilePage
        from ofscraper.gui.dialogs.merge_dialog import MergePage
        from ofscraper.gui.dialogs.drm_dialog import DRMKeyPage

        # Scraper workflow pages (nested in a sub-stack)
        self.scraper_stack = _PageStack(self.stack)

        self.action_page = ActionPage(self.scraper_stack, manager=self.manager)
        self.model_page = ModelSelectorPage(self.scraper_stack, manager=self.manager)
        self.area_page = AreaSelectorPage(self.scraper_stack, manager=self.manager)
        self.table_page = TablePage(self.scraper_stack, manager=self.manager)

        self.scraper_stack.add_page(0, self.action_page)
        self.scraper_stack.add_page(1, self.model_page)
        self.scraper_stack.add_page(2, self.area_page)
        self.scraper_stack.add_page(3, self.table_page)
        self.scraper_stack._show_page(0)

        self._add_page("scraper", self.scraper_stack)
        self._add_page("auth", AuthPage(self.stack, manager=self.manager))
        self._add_page("config", ConfigPage(self.stack, manager=self.manager))
        self._add_page("drm", DRMKeyPage(self.stack, manager=self.manager))
        self._add_page("profiles", ProfilePage(self.stack, manager=self.manager))
        self._add_page("merge", MergePage(self.stack, manager=self.manager))
        self._add_page("help", HelpPage(self.stack, manager=self.manager))

    def _add_page(self, page_id, widget):
        self._pages[page_id] = widget
        self.stack.add_page(page_id, widget)

    def _connect_signals(self):
        app_signals.navigate_to_page.connect(self._on_navigate_signal)
        app_signals.status_message.connect(self._on_status_message)
        app_signals.error_occurred.connect(self._on_error)
        app_signals.help_anchor_requested.connect(self._on_help_anchor_requested)

        # Scraper workflow navigation
        app_signals.action_selected.connect(self._on_action_selected)
        app_signals.models_selected.connect(self._on_models_selected)
        app_signals.areas_selected.connect(self._on_areas_selected)
        app_signals.data_loading_finished.connect(self._on_data_loaded)
        app_signals.data_replace.connect(self._on_data_replace)

    def _navigate(self, page_id):
        if page_id in self._pages:
            self.stack._show_page(page_id)
            # Update nav button active states
            for pid, btn in self._nav_buttons.items():
                btn.set_active(pid == page_id)

    def _on_navigate_signal(self, page_id):
        self._navigate(page_id)

    def _on_help_anchor_requested(self, anchor):
        try:
            self._navigate("help")
            help_page = self._pages.get("help")
            if help_page and hasattr(help_page, "scroll_to_anchor"):
                self.after(0, lambda: help_page.scroll_to_anchor(str(anchor)))
        except Exception:
            pass

    def _on_status_message(self, message):
        self._status_label.configure(text=message)
        # Auto-clear after 5 seconds
        self.after(5000, lambda: self._status_label.configure(text="Ready"))

    def _on_error(self, title, message):
        messagebox.showerror(title, message)

    def _on_action_selected(self, actions):
        """Move from action page to area/filter configuration page."""
        self.scraper_stack._show_page(2)  # area page

    def _on_models_selected(self, models):
        """Move from model selection to table page."""
        self.scraper_stack._show_page(3)  # table page
        self.table_page.show_sidebar()
        # Copy filter state from area page to table page sidebar
        self.area_page.copy_filter_state_to(self.table_page.sidebar)
        _check_modes = {"post_check", "msg_check", "paid_check", "story_check"}
        _subscribe_mode = {"subscribe"}
        _current = getattr(self.area_page, "_current_actions", set()) or set()
        if bool(_current & _check_modes):
            app_signals.status_message.emit("Checking -- fetching data, please wait...")
        elif bool(_current & _subscribe_mode):
            app_signals.status_message.emit("Subscribing to free accounts, please wait...")
        else:
            app_signals.status_message.emit("Click Start Scraping to begin")

    def _on_areas_selected(self, areas):
        """Areas selected -- begin scraping."""
        app_signals.status_message.emit("Loading data...")

    def _on_data_loaded(self, table_data):
        """Data loaded for a user -- append to table."""
        self.table_page.append_data(table_data)

    def _on_data_replace(self, table_data):
        """DB fallback loaded -- replace table with authoritative DB rows."""
        self.table_page.load_data(table_data)

    def go_to_scraper_step(self, step_index):
        """Navigate to a specific step in the scraper workflow."""
        if step_index in self.scraper_stack._pages:
            self.scraper_stack._show_page(step_index)

    def _maybe_show_missing_dependency_notice(self):
        """Popup a notice if FFmpeg or manual CDM key paths are missing."""
        if getattr(self, "_missing_deps_notice_shown", False):
            return
        self._missing_deps_notice_shown = True

        try:
            from ofscraper.utils.config.config import read_config
            cfg = read_config(update=False) or {}
        except Exception:
            cfg = {}

        ffmpeg_path = None
        try:
            if isinstance(cfg.get("binary_options"), dict):
                ffmpeg_path = (cfg.get("binary_options") or {}).get("ffmpeg")
        except Exception:
            pass
        cdm_client = (
            (cfg.get("cdm_options") or {}).get("client-id")
            if isinstance(cfg.get("cdm_options"), dict)
            else None
        )
        cdm_private = (
            (cfg.get("cdm_options") or {}).get("private-key")
            if isinstance(cfg.get("cdm_options"), dict)
            else None
        )

        from pathlib import Path

        ffmpeg_raw = (str(ffmpeg_path).strip() if ffmpeg_path is not None else "")
        missing_ffmpeg = True
        if ffmpeg_raw:
            try:
                p = Path(ffmpeg_raw)
                missing_ffmpeg = not p.is_file()
            except Exception:
                missing_ffmpeg = True

        cdm_opts = cfg.get("cdm_options") if isinstance(cfg.get("cdm_options"), dict) else {}
        key_mode = str(cdm_opts.get("key-mode-default") or "cdrm").lower().strip() or "cdrm"
        missing_manual_cdm = False
        if key_mode == "manual":
            client_raw = str(cdm_client).strip() if cdm_client is not None else ""
            priv_raw = str(cdm_private).strip() if cdm_private is not None else ""
            missing_manual_cdm = True
            if client_raw and priv_raw:
                try:
                    missing_manual_cdm = not (Path(client_raw).is_file() and Path(priv_raw).is_file())
                except Exception:
                    missing_manual_cdm = True

        if not (missing_ffmpeg or missing_manual_cdm):
            return

        def open_ffmpeg():
            try:
                self._navigate("config")
                page = self._pages.get("config")
                if page and hasattr(page, "go_to_config_field"):
                    page.go_to_config_field("Download", "ffmpeg")
            except Exception:
                pass

        def open_cdm():
            try:
                self._navigate("config")
                page = self._pages.get("config")
                if page and hasattr(page, "go_to_config_field"):
                    key = "client-id" if not bool(client_raw) else "private-key"
                    page.go_to_config_field("CDM", key)
            except Exception:
                pass

        def open_drm():
            try:
                self._navigate("drm")
            except Exception:
                pass

        try:
            from ofscraper.gui.dialogs.missing_deps_dialog import MissingDepsDialog
            dlg = MissingDepsDialog(
                missing_ffmpeg=missing_ffmpeg,
                missing_manual_cdm=missing_manual_cdm,
                on_open_ffmpeg=open_ffmpeg,
                on_open_cdm=open_cdm,
                on_open_drm=open_drm,
                parent=self._root,
            )
            # Modal dialog — waits until closed
        except Exception as e:
            log.debug(f"Missing deps dialog failed: {e}")
