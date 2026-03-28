import logging
import tkinter as tk
from tkinter import ttk, messagebox

from ofscraper.gui.signals import app_signals
from ofscraper.gui.utils.thread_worker import Worker
from ofscraper.gui.widgets.sidebar import FilterSidebar
import ofscraper.utils.config.data as config_data

log = logging.getLogger("shared")

DOWNLOAD_AREAS = [
    "Profile", "Timeline", "Pinned", "Archived", "Highlights",
    "Stories", "Messages", "Purchased", "Streams", "Labels",
]

LIKE_AREAS = ["Timeline", "Pinned", "Archived", "Streams", "Labels"]

POST_CHECK_AREAS = ["Timeline", "Pinned", "Archived", "Labels", "Streams"]

_CHECK_MODES = {"post_check", "msg_check", "paid_check", "story_check"}
_NO_AREA_MODES = {"msg_check", "paid_check", "story_check", "subscribe"}


class AreaSelectorPage(ttk.Frame):
    """Content area + filter configuration page."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._current_actions = set()
        self._area_checks = {}
        self._models_loading = False
        self._models_loaded = False
        self._models_error = None
        self._loaded_model_count = 0
        self._setup_ui()
        self._connect_signals()
        self._refresh_discord_option_state()

    def _setup_ui(self):
        # Outer: scrollable content + fixed nav bar at bottom
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        # Scrollable content area
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_window, width=e.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas_frame = ttk.Frame(self)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, in_=canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, in_=canvas_frame)

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        content = scroll_frame

        # Header
        ttk.Label(content, text="Select Content Areas & Filters",
                  style="Heading.TLabel").pack(anchor=tk.W, padx=24, pady=(24, 4))
        ttk.Label(content, text="Configure what to scrape and how to filter results.",
                  style="Subheading.TLabel").pack(anchor=tk.W, padx=24)

        # Areas group
        self.areas_group = ttk.LabelFrame(content, text="Content Areas")
        self.areas_group.pack(fill=tk.X, padx=24, pady=(12, 4))

        areas_inner = ttk.Frame(self.areas_group)
        areas_inner.pack(fill=tk.X, padx=8, pady=8)
        for i, area in enumerate(DOWNLOAD_AREAS):
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(areas_inner, text=area, variable=var)
            row = i // 3
            col = i % 3
            cb.grid(row=row, column=col, sticky=tk.W, padx=8, pady=2)
            self._area_checks[area] = (cb, var)

        # Bulk buttons
        bulk_frame = ttk.Frame(content)
        bulk_frame.pack(fill=tk.X, padx=24, pady=4)
        ttk.Button(bulk_frame, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(bulk_frame, text="Deselect All", command=self._deselect_all).pack(side=tk.LEFT)

        # Media Types group
        ttk.Separator(content, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=24, pady=8)

        media_group = ttk.LabelFrame(content, text="Media Types to Download")
        media_group.pack(fill=tk.X, padx=24, pady=4)

        config_filter = config_data.get_filter() or ["Images", "Videos", "Audios"]
        config_filter_lower = {x.lower() for x in config_filter}

        media_inner = ttk.Frame(media_group)
        media_inner.pack(fill=tk.X, padx=8, pady=8)
        self._mediatype_checks = {}
        for mt in ["Images", "Videos", "Audios"]:
            var = tk.BooleanVar(value=mt.lower() in config_filter_lower)
            cb = ttk.Checkbutton(media_inner, text=mt, variable=var)
            cb.pack(side=tk.LEFT, padx=(0, 16))
            self._mediatype_checks[mt] = (cb, var)

        # Extra options
        ttk.Separator(content, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=24, pady=8)

        extras_group = ttk.LabelFrame(content, text="Additional Options")
        extras_group.pack(fill=tk.X, padx=24, pady=4)

        self._scrape_paid_var = tk.BooleanVar(value=False)
        self.scrape_paid_check = ttk.Checkbutton(
            extras_group,
            text="Scrape entire paid page (slower but more comprehensive)",
            variable=self._scrape_paid_var,
        )
        self.scrape_paid_check.pack(anchor=tk.W, padx=8, pady=2)

        self._scrape_labels_var = tk.BooleanVar(value=False)
        self.scrape_labels_check = ttk.Checkbutton(
            extras_group,
            text="Scrape labels",
            variable=self._scrape_labels_var,
        )
        self.scrape_labels_check.pack(anchor=tk.W, padx=8, pady=2)

        self._discord_var = tk.BooleanVar(value=False)
        self.discord_updates_check = ttk.Checkbutton(
            extras_group,
            text="Send updates to Discord (requires webhook URL in Config)",
            variable=self._discord_var,
        )
        self.discord_updates_check.pack(anchor=tk.W, padx=8, pady=(2, 8))

        # Advanced options
        adv_group = ttk.LabelFrame(content, text="Advanced Scrape Options")
        adv_group.pack(fill=tk.X, padx=24, pady=4)

        self._allow_dupes_var = tk.BooleanVar(value=False)
        self.allow_dupes_check = ttk.Checkbutton(
            adv_group,
            text="Allow duplicates (do NOT skip duplicates; treat reposts as new items)",
            variable=self._allow_dupes_var,
        )
        self.allow_dupes_check.pack(anchor=tk.W, padx=8, pady=2)

        self._rescrape_var = tk.BooleanVar(value=False)
        self.rescrape_all_check = ttk.Checkbutton(
            adv_group,
            text="Rescrape everything (ignore cache / scan from the beginning)",
            variable=self._rescrape_var,
            command=self._on_rescrape_toggled,
        )
        self.rescrape_all_check.pack(anchor=tk.W, padx=8, pady=2)

        self._delete_db_var = tk.BooleanVar(value=False)
        self.delete_db_check = ttk.Checkbutton(
            adv_group,
            text="Delete model DB before scraping (resets downloaded/unlocked history)",
            variable=self._delete_db_var,
            state=tk.DISABLED,
        )
        self.delete_db_check.pack(anchor=tk.W, padx=8, pady=2)

        self._delete_dl_var = tk.BooleanVar(value=False)
        self.delete_downloads_check = ttk.Checkbutton(
            adv_group,
            text="Also delete existing downloaded files for selected models",
            variable=self._delete_dl_var,
            state=tk.DISABLED,
            command=self._on_delete_downloads_toggled,
        )
        self.delete_downloads_check.pack(anchor=tk.W, padx=8, pady=(2, 4))

        ttk.Label(
            adv_group,
            text="Tip: deleting files uses your model DB to locate paths, so keep the DB delete option enabled.",
            style="Muted.TLabel",
            wraplength=500,
        ).pack(anchor=tk.W, padx=8, pady=(0, 8))

        # Daemon mode
        ttk.Separator(content, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=24, pady=8)

        daemon_group = ttk.LabelFrame(content, text="Daemon Mode (Auto-Repeat Scraping)")
        daemon_group.pack(fill=tk.X, padx=24, pady=4)

        self._daemon_var = tk.BooleanVar(value=False)
        self.daemon_check = ttk.Checkbutton(
            daemon_group,
            text="Enable daemon mode (automatically re-scrape on a schedule)",
            variable=self._daemon_var,
            command=self._on_daemon_toggled,
        )
        self.daemon_check.pack(anchor=tk.W, padx=8, pady=2)

        interval_frame = ttk.Frame(daemon_group)
        interval_frame.pack(fill=tk.X, padx=8, pady=2)
        ttk.Label(interval_frame, text="Interval:").pack(side=tk.LEFT, padx=(0, 4))
        self._daemon_interval_var = tk.DoubleVar(value=30.0)
        self.daemon_interval = ttk.Spinbox(
            interval_frame, textvariable=self._daemon_interval_var,
            from_=1.0, to=1440.0, increment=5.0, width=10, state=tk.DISABLED,
        )
        self.daemon_interval.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(interval_frame, text="minutes").pack(side=tk.LEFT)

        self._notify_var = tk.BooleanVar(value=False)
        self.notify_check = ttk.Checkbutton(
            daemon_group, text="System notification when scraping starts",
            variable=self._notify_var,
        )
        self.notify_check.pack(anchor=tk.W, padx=8, pady=2)

        self._sound_var = tk.BooleanVar(value=False)
        self.sound_check = ttk.Checkbutton(
            daemon_group, text="Sound alert when scraping starts",
            variable=self._sound_var,
        )
        self.sound_check.pack(anchor=tk.W, padx=8, pady=(2, 8))

        # Separator before filters
        ttk.Separator(content, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=24, pady=8)

        # Filter widgets embedded inline
        self.filter_sidebar = FilterSidebar(content, embedded=True)
        self.filter_sidebar.pack(fill=tk.X, padx=16, pady=(0, 16))

        # Bottom navigation bar
        nav_bar = ttk.Frame(self, style="Toolbar.TFrame")
        nav_bar.grid(row=1, column=0, sticky="ew")

        ttk.Button(nav_bar, text="<< Back", command=self._on_back).pack(
            side=tk.LEFT, padx=(24, 8), pady=8
        )

        # Model loading indicator
        self._model_loading_bar = ttk.Progressbar(
            nav_bar, orient=tk.HORIZONTAL, mode="indeterminate", length=120
        )
        self._model_loading_label = ttk.Label(nav_bar, text="", style="Muted.TLabel")
        self._retry_models_btn = ttk.Button(
            nav_bar, text="Retry Loading Models", command=self._retry_model_load
        )

        self.next_btn = ttk.Button(
            nav_bar, text="Next: Select Models  >>",
            style="Primary.TButton", command=self._on_next,
        )
        self.next_btn.pack(side=tk.LEFT, padx=8, pady=8)

    def _connect_signals(self):
        app_signals.action_selected.connect(self._on_action_selected)

    def _refresh_discord_option_state(self):
        try:
            url = (config_data.get_discord() or "").strip()
        except Exception:
            url = ""
        has_webhook = bool(url)
        try:
            self.discord_updates_check.configure(
                state=tk.NORMAL if has_webhook else tk.DISABLED
            )
            if not has_webhook:
                self._discord_var.set(False)
        except Exception:
            pass

    def reset_to_defaults(self):
        for _, var in self._area_checks.values():
            var.set(True)
        self._scrape_paid_var.set(False)
        self._scrape_labels_var.set(False)
        self._discord_var.set(False)
        self._allow_dupes_var.set(False)
        self._rescrape_var.set(False)
        self._delete_db_var.set(False)
        self._delete_dl_var.set(False)
        self._daemon_var.set(False)
        self._daemon_interval_var.set(30.0)
        self.daemon_interval.configure(state=tk.DISABLED)
        self._notify_var.set(False)
        self._sound_var.set(False)
        # Reset media type checkboxes to match config
        config_filter = config_data.get_filter() or ["Images", "Videos", "Audios"]
        config_filter_lower = {x.lower() for x in config_filter}
        for mt, (cb, var) in self._mediatype_checks.items():
            var.set(mt.lower() in config_filter_lower)
        self.filter_sidebar.reset_all()
        self._models_loaded = False
        self._models_loading = False
        self._refresh_discord_option_state()

    def _on_action_selected(self, actions):
        self._current_actions = actions
        self._update_available_areas()
        self._start_model_load()

    def _on_rescrape_toggled(self):
        checked = self._rescrape_var.get()
        self.delete_db_check.configure(state=tk.NORMAL if checked else tk.DISABLED)
        self.delete_downloads_check.configure(state=tk.NORMAL if checked else tk.DISABLED)
        if not checked:
            self._delete_db_var.set(False)
            self._delete_dl_var.set(False)

    def _on_delete_downloads_toggled(self):
        if self._delete_dl_var.get():
            self._delete_db_var.set(True)

    def _on_daemon_toggled(self):
        self.daemon_interval.configure(
            state=tk.NORMAL if self._daemon_var.get() else tk.DISABLED
        )

    def _retry_model_load(self):
        self._models_loaded = False
        self._models_loading = False
        self._retry_models_btn.pack_forget()
        self._start_model_load()

    def _start_model_load(self):
        if self._models_loading or self._models_loaded:
            return

        self._models_loading = True
        self._models_error = None
        self._loaded_model_count = 0
        self._retry_models_btn.pack_forget()

        self.next_btn.configure(state=tk.DISABLED)
        self._model_loading_label.configure(text="Loading models from API...")
        self._model_loading_label.pack(side=tk.LEFT, padx=4, pady=8)
        self._model_loading_bar.pack(side=tk.LEFT, padx=4, pady=8)
        self._model_loading_bar.start(15)

        if not (self.manager and getattr(self.manager, "model_manager", None)):
            self._models_loading = False
            self._models_error = "Model manager not available"
            self._model_loading_bar.stop()
            self._model_loading_bar.pack_forget()
            self._model_loading_label.configure(text="Model manager not available")
            self.next_btn.configure(state=tk.NORMAL)
            return

        worker = Worker(self._fetch_models)
        worker.signals.finished.connect(self._on_models_loaded)
        worker.signals.error.connect(self._on_models_error)
        worker.start()

    def _fetch_models(self):
        import asyncio
        import ofscraper.data.models.utils.retriver as retriver
        import ofscraper.utils.paths.common as common_paths
        import ofscraper.utils.auth.utils.dict as auth_dict_mod

        try:
            auth_path = common_paths.get_auth_file()
            log.info(f"[GUI retry] Auth file path: {auth_path}")
            auth_data = auth_dict_mod.get_auth_dict()
            filled = {k: ("set" if v else "EMPTY") for k, v in auth_data.items()}
            log.info(f"[GUI retry] Auth field status: {filled}")

            required = ["sess", "auth_id", "user_agent", "x-bc"]
            missing = [k for k in required if not auth_data.get(k)]
            if missing:
                raise Exception(
                    f"Auth fields not configured: {', '.join(missing)}. "
                    "Please fill in your auth credentials first."
                )
        except Exception as e:
            log.warning(f"[GUI retry] Auth check failed: {e}")
            raise

        self.manager.model_manager._all_subs_dict = {}

        import ofscraper.utils.profiles.data as profile_data
        profile_data.currentData = None
        profile_data.currentProfile = None

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(retriver.get_models())
            self.manager.model_manager.all_subs_dict = data
        finally:
            loop.close()
            asyncio.set_event_loop(None)

        return getattr(self.manager.model_manager, "all_subs_obj", None) or []

    def _on_models_loaded(self, models):
        self._models_loading = False
        self._loaded_model_count = len(models or [])
        self._model_loading_bar.stop()
        self._model_loading_bar.pack_forget()
        if self._loaded_model_count == 0:
            self._models_loaded = False
            self._show_auth_failure_prompt()
            return
        self._models_loaded = True
        self._retry_models_btn.pack_forget()
        self._model_loading_label.configure(text=f"Models loaded: {self._loaded_model_count}")
        self.next_btn.configure(state=tk.NORMAL)

    def _on_models_error(self, error_msg):
        self._models_loading = False
        self._models_loaded = False
        self._models_error = error_msg
        self._model_loading_bar.stop()
        self._model_loading_bar.pack_forget()
        self._show_auth_failure_prompt(error_msg)

    def _show_auth_failure_prompt(self, detail=None):
        self._model_loading_label.configure(text="Unable to get list of models.")
        self._retry_models_btn.pack(side=tk.LEFT, padx=4, pady=8)
        self.next_btn.configure(state=tk.DISABLED)

        msg = (
            "Unable to get list of models.\n"
            "Please check your auth information.\n\n"
            "If your auth is correct and the issue persists,\n"
            "try changing the Dynamic Mode in Configuration > Advanced."
        )
        if detail:
            msg += f"\n\nDetails: {detail}"

        result = messagebox.askretrycancel("Unable to Load Models", msg)
        if result:
            self._retry_model_load()

    def _update_available_areas(self):
        is_check = bool(self._current_actions & _CHECK_MODES)
        is_no_area = bool(self._current_actions & _NO_AREA_MODES)

        if is_no_area and not is_check:
            self.areas_group.pack_forget()
            for area, (cb, var) in self._area_checks.items():
                var.set(False)
                cb.configure(state=tk.DISABLED)
            return
        elif is_check:
            if "post_check" in self._current_actions:
                available = POST_CHECK_AREAS
                self.areas_group.configure(text="Check Areas")
                try:
                    self.areas_group.pack(fill=tk.X, padx=24, pady=(12, 4))
                except Exception:
                    pass
            else:
                self.areas_group.pack_forget()
                for area, (cb, var) in self._area_checks.items():
                    var.set(False)
                    cb.configure(state=tk.DISABLED)
                return
        else:
            has_download = "download" in self._current_actions
            has_like = "like" in self._current_actions or "unlike" in self._current_actions
            if has_download:
                available = DOWNLOAD_AREAS
            elif has_like:
                available = LIKE_AREAS
            else:
                available = DOWNLOAD_AREAS
            self.areas_group.configure(text="Content Areas")
            try:
                self.areas_group.pack(fill=tk.X, padx=24, pady=(12, 4))
            except Exception:
                pass

        for area, (cb, var) in self._area_checks.items():
            if area in available:
                cb.configure(state=tk.NORMAL)
            else:
                cb.configure(state=tk.DISABLED)
                var.set(False)

    def _select_all(self):
        for area, (cb, var) in self._area_checks.items():
            if str(cb.cget("state")) != "disabled":
                var.set(True)

    def _deselect_all(self):
        for area, (cb, var) in self._area_checks.items():
            if str(cb.cget("state")) != "disabled":
                var.set(False)

    def get_selected_areas(self):
        return [
            area for area, (cb, var) in self._area_checks.items()
            if var.get() and str(cb.cget("state")) != "disabled"
        ]

    def get_selected_mediatypes(self):
        selected = [mt for mt, (cb, var) in self._mediatype_checks.items() if var.get()]
        return selected if selected else ["Images", "Videos", "Audios"]

    def is_daemon_enabled(self):
        return self._daemon_var.get()

    def get_daemon_interval(self):
        return self._daemon_interval_var.get()

    def is_notify_enabled(self):
        return self._notify_var.get()

    def is_sound_enabled(self):
        return self._sound_var.get()

    def get_username_filter(self):
        return self.filter_sidebar.username_input.text().strip()

    def copy_filter_state_to(self, target_sidebar):
        """Copy the filter configuration from this page's sidebar to the target sidebar."""
        src = self.filter_sidebar
        tgt = target_sidebar

        tgt.text_input.setText(src.text_input.text())
        tgt.fullstring_check.setChecked(src.fullstring_check.isChecked())

        for mt, cb in src.media_checks.items():
            if mt in tgt.media_checks:
                tgt.media_checks[mt].setChecked(cb.isChecked())

        for rt, cb in src.resp_checks.items():
            if rt in tgt.resp_checks:
                tgt.resp_checks[rt].setChecked(cb.isChecked())

        tgt.dl_true.setChecked(src.dl_true.isChecked())
        tgt.dl_false.setChecked(src.dl_false.isChecked())
        tgt.dl_no.setChecked(src.dl_no.isChecked())
        tgt.ul_true.setChecked(src.ul_true.isChecked())
        tgt.ul_false.setChecked(src.ul_false.isChecked())
        tgt.ul_not_paid.setChecked(src.ul_not_paid.isChecked())

        tgt.date_enabled.setChecked(src.date_enabled.isChecked())
        tgt.min_date.setDate(src.min_date)
        tgt.max_date.setDate(src.max_date)

        tgt.length_enabled.setChecked(src.length_enabled.isChecked())
        tgt.min_time.setTime(src.min_time.time_str())
        tgt.max_time.setTime(src.max_time.time_str())

        tgt.price_min.setValue(src.price_min.value())
        tgt.price_max.setValue(src.price_max.value())

        tgt.media_id_input.setText(src.media_id_input.text())
        tgt.post_id_input.setText(src.post_id_input.text())
        tgt.post_media_count_input.setValue(src.post_media_count_input.value())
        tgt.other_posts_input.setValue(src.other_posts_input.value())

        tgt.username_input.setText(src.username_input.text())

    def _on_back(self):
        # Navigate back to action page (index 0 in scraper_stack)
        parent_stack = self.master
        if parent_stack and hasattr(parent_stack, "_show_page"):
            parent_stack._show_page(0)

    def _on_next(self):
        is_check = bool(self._current_actions & _CHECK_MODES)
        is_subscribe = bool(self._current_actions & _NO_AREA_MODES)
        needs_areas = (not is_check and not is_subscribe) or "post_check" in self._current_actions

        selected = self.get_selected_areas()
        if needs_areas and not selected:
            app_signals.error_occurred.emit(
                "No Areas Selected",
                "Please select at least one content area.",
            )
            return

        log.info(f"Areas configured: {selected}")
        mediatypes = self.get_selected_mediatypes()
        app_signals.mediatypes_configured.emit(mediatypes)

        if is_check:
            app_signals.areas_selected.emit(selected)

        username = self.get_username_filter()
        parent_stack = self.master
        if parent_stack and hasattr(parent_stack, "_show_page"):
            # Get model selector page and apply username filter
            model_page = parent_stack._pages.get(1)
            if model_page and hasattr(model_page, "pre_filter_username"):
                model_page.pre_filter_username(username)
            parent_stack._show_page(1)
