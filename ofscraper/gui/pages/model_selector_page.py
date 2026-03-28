import logging
import tkinter as tk
from tkinter import ttk, messagebox

from ofscraper.gui.signals import app_signals
from ofscraper.gui.utils.thread_worker import Worker

log = logging.getLogger("shared")

SORT_OPTIONS = [
    ("Name", "name"),
    ("Last Seen", "last-seen"),
    ("Expired", "expired"),
    ("Subscribed", "subscribed"),
    ("Current Price", "current-price"),
    ("Promo Price", "promo-price"),
    ("Renewal Price", "renewal-price"),
    ("Regular Price", "regular-price"),
]


class ModelSelectorPage(ttk.Frame):
    """Model/creator selection page with search and filtering."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._all_models = {}  # name -> model object
        self._filtered_names = []
        self._checked = set()  # set of checked model names
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 4))
        ttk.Label(header_frame, text="Select Models", style="Heading.TLabel").pack(anchor=tk.W)
        ttk.Label(header_frame, text="Search and select the creators you want to process.",
                  style="Subheading.TLabel").pack(anchor=tk.W)

        # Search + bulk buttons
        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="ew", padx=24, pady=(8, 4))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._filter_list())
        search_entry = ttk.Entry(controls, textvariable=self._search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(controls, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Deselect All", command=self._deselect_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Toggle", command=self._toggle_all).pack(side=tk.LEFT, padx=2)

        self.count_label = ttk.Label(controls, text="0 / 0 selected", style="Muted.TLabel")
        self.count_label.pack(side=tk.RIGHT)

        # Main content: paned window with list + filter panel
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.grid(row=2, column=0, sticky="nsew", padx=24, pady=4)

        # Left: model list (Treeview with checkmarks in display column)
        left_frame = ttk.Frame(paned)

        # Loading label
        self.loading_label = ttk.Label(left_frame, text="Loading models...",
                                       style="Subheading.TLabel")
        self.retry_btn = ttk.Button(left_frame, text="Retry Loading Models",
                                    style="Primary.TButton", command=self._load_models)

        # Model listbox (using Treeview for better control)
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.model_tree = ttk.Treeview(
            list_frame, columns=("check", "display"), show="headings",
            selectmode="browse",
        )
        self.model_tree.heading("check", text="Sel")
        self.model_tree.heading("display", text="Model")
        self.model_tree.column("check", width=40, minwidth=40, stretch=False)
        self.model_tree.column("display", width=500, minwidth=200, stretch=True)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=vsb.set)
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.model_tree.bind("<ButtonRelease-1>", self._on_tree_click)

        paned.add(left_frame, weight=3)

        # Right: filter panel
        right_frame = ttk.Frame(paned)

        ttk.Label(right_frame, text="Filters", font=("Segoe UI", 14, "bold")).pack(
            anchor=tk.W, padx=8, pady=(0, 8)
        )

        # Subscription type
        sub_group = ttk.LabelFrame(right_frame, text="Subscription Type")
        sub_group.pack(fill=tk.X, padx=8, pady=4)

        sub_inner = ttk.Frame(sub_group)
        sub_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(sub_inner, text="Renewal:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self._renewal_var = tk.StringVar(value="All")
        self.renewal_combo = ttk.Combobox(
            sub_inner, textvariable=self._renewal_var,
            values=["All", "Renewal On", "Renewal Off"], state="readonly", width=14
        )
        self.renewal_combo.grid(row=0, column=1, sticky=tk.EW, padx=(4, 0), pady=2)

        ttk.Label(sub_inner, text="Status:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self._status_var = tk.StringVar(value="All")
        self.status_combo = ttk.Combobox(
            sub_inner, textvariable=self._status_var,
            values=["All", "Active Only", "Expired Only"], state="readonly", width=14
        )
        self.status_combo.grid(row=1, column=1, sticky=tk.EW, padx=(4, 0), pady=2)
        sub_inner.columnconfigure(1, weight=1)

        # Promo / flags
        flags_group = ttk.LabelFrame(right_frame, text="Flags")
        flags_group.pack(fill=tk.X, padx=8, pady=4)

        flags_inner = ttk.Frame(flags_group)
        flags_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(flags_inner, text="Promo:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self._promo_var = tk.StringVar(value="All")
        self.promo_combo = ttk.Combobox(
            flags_inner, textvariable=self._promo_var,
            values=["All", "Has Claimable Promo", "No Promo"], state="readonly", width=18
        )
        self.promo_combo.grid(row=0, column=1, sticky=tk.EW, padx=(4, 0), pady=2)

        ttk.Label(flags_inner, text="Free Trial:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self._free_trial_var = tk.StringVar(value="All")
        self.free_trial_combo = ttk.Combobox(
            flags_inner, textvariable=self._free_trial_var,
            values=["All", "Free Trial Only", "No Free Trial"], state="readonly", width=18
        )
        self.free_trial_combo.grid(row=1, column=1, sticky=tk.EW, padx=(4, 0), pady=2)

        ttk.Label(flags_inner, text="Last Seen:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self._last_seen_var = tk.StringVar(value="All")
        self.last_seen_combo = ttk.Combobox(
            flags_inner, textvariable=self._last_seen_var,
            values=["All", "Visible", "Hidden"], state="readonly", width=18
        )
        self.last_seen_combo.grid(row=2, column=1, sticky=tk.EW, padx=(4, 0), pady=2)
        flags_inner.columnconfigure(1, weight=1)

        # Price range
        price_group = ttk.LabelFrame(right_frame, text="Price Range")
        price_group.pack(fill=tk.X, padx=8, pady=4)

        price_inner = ttk.Frame(price_group)
        price_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(price_inner, text="Min:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self._price_min_var = tk.DoubleVar(value=0)
        self.price_min = ttk.Spinbox(
            price_inner, textvariable=self._price_min_var,
            from_=0, to=99999, increment=1.0, width=10
        )
        self.price_min.grid(row=0, column=1, sticky=tk.EW, padx=(4, 0), pady=2)

        ttk.Label(price_inner, text="Max:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self._price_max_var = tk.DoubleVar(value=0)
        self.price_max = ttk.Spinbox(
            price_inner, textvariable=self._price_max_var,
            from_=0, to=99999, increment=1.0, width=10
        )
        self.price_max.grid(row=1, column=1, sticky=tk.EW, padx=(4, 0), pady=2)
        price_inner.columnconfigure(1, weight=1)

        # Sort
        sort_group = ttk.LabelFrame(right_frame, text="Sort")
        sort_group.pack(fill=tk.X, padx=8, pady=4)

        sort_inner = ttk.Frame(sort_group)
        sort_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(sort_inner, text="Sort by:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self._sort_var = tk.StringVar(value=SORT_OPTIONS[0][0])
        self.sort_combo = ttk.Combobox(
            sort_inner, textvariable=self._sort_var,
            values=[s[0] for s in SORT_OPTIONS], state="readonly", width=14
        )
        self.sort_combo.grid(row=0, column=1, sticky=tk.EW, padx=(4, 0), pady=2)

        self._sort_desc_var = tk.BooleanVar(value=False)
        self.sort_desc_check = ttk.Checkbutton(
            sort_inner, text="Descending", variable=self._sort_desc_var
        )
        self.sort_desc_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        sort_inner.columnconfigure(1, weight=1)

        # Filter buttons
        ttk.Button(right_frame, text="Apply Filters", style="Primary.TButton",
                   command=self._apply_filters).pack(fill=tk.X, padx=8, pady=4)
        ttk.Button(right_frame, text="Reset Filters",
                   command=self._reset_filters).pack(fill=tk.X, padx=8, pady=4)

        paned.add(right_frame, weight=1)

        # Bottom navigation
        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(8, 24))

        ttk.Button(nav_frame, text="<< Back", command=self._on_back).pack(side=tk.LEFT)
        self.next_btn = ttk.Button(nav_frame, text="Next  >>",
                                   style="Primary.TButton", command=self._on_next)
        self.next_btn.pack(side=tk.RIGHT)

    def _connect_signals(self):
        pass  # Models are loaded on the areas page

    def populate_from_manager(self):
        """Populate list from already-fetched manager state (no API calls)."""
        self.model_tree.delete(*self.model_tree.get_children())
        self.loading_label.pack_forget()
        self.next_btn.configure(state=tk.NORMAL)

        if not (self.manager and self.manager.model_manager):
            self.loading_label.configure(text="Model manager not available. Showing empty list.")
            self.loading_label.pack(anchor=tk.CENTER, pady=20)
            return

        models = getattr(self.manager.model_manager, "all_subs_obj", None) or []
        if models:
            self._all_models = {m.name: m for m in models}
            self._populate_list(sorted(self._all_models.keys()))
            self.retry_btn.pack_forget()
            app_signals.status_message.emit(f"Loaded {len(models)} models")
        else:
            self._all_models = {}
            self.loading_label.configure(text="No models loaded. Check your auth and click Retry.")
            self.loading_label.pack(anchor=tk.CENTER, pady=20)
            self.retry_btn.pack(anchor=tk.CENTER, pady=8)
            self.next_btn.configure(state=tk.DISABLED)

    def _load_models(self):
        self.model_tree.delete(*self.model_tree.get_children())
        self.retry_btn.pack_forget()
        self.loading_label.configure(text="Loading models from API...")
        self.loading_label.pack(anchor=tk.CENTER, pady=20)
        self.next_btn.configure(state=tk.DISABLED)

        if not (self.manager and self.manager.model_manager):
            self.loading_label.configure(text="Model manager not available.")
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

        return self.manager.model_manager.all_subs_obj

    def _on_models_loaded(self, models):
        self.loading_label.pack_forget()
        self.retry_btn.pack_forget()
        self.next_btn.configure(state=tk.NORMAL)
        if models:
            self._all_models = {m.name: m for m in models}
            self._populate_list(sorted(self._all_models.keys()))
            app_signals.status_message.emit(f"Loaded {len(models)} models")
        else:
            self._all_models = {}
            self._show_auth_failure_prompt()

    def _on_models_error(self, error_msg):
        log.error(f"Model fetch error: {error_msg}")
        self._show_auth_failure_prompt(error_msg)

    def _show_auth_failure_prompt(self, detail=None):
        self.loading_label.configure(text="Unable to get list of models.")
        self.loading_label.pack(anchor=tk.CENTER, pady=20)
        self.retry_btn.pack(anchor=tk.CENTER, pady=8)
        self.next_btn.configure(state=tk.DISABLED)

        msg = "Unable to get list of models.\nPlease check your auth information."
        if detail:
            msg += f"\n\nDetails: {detail}"

        result = messagebox.askretrycancel("Unable to Load Models", msg)
        if result:
            self._load_models()
        else:
            app_signals.navigate_to_page.emit("auth")

    def _populate_list(self, names):
        """Populate the treeview with model names and details."""
        self.model_tree.delete(*self.model_tree.get_children())
        for name in names:
            model = self._all_models.get(name)
            if model:
                sub_date = getattr(model, "subscribed_string", None) or "N/A"
                price = getattr(model, "final_current_price", 0) or 0
                display = f"{name}  =>  subscribed date: {sub_date} | current_price: {price}"
            else:
                display = name

            check_mark = "[x]" if name in self._checked else "[ ]"
            self.model_tree.insert("", tk.END, iid=name, values=(check_mark, display))

        self._update_count()
        # Re-apply any active search text
        current_text = self._search_var.get()
        if current_text:
            self._filter_list()

    def _on_tree_click(self, event):
        """Toggle check state on click."""
        item_id = self.model_tree.identify_row(event.y)
        if not item_id:
            return

        name = item_id
        if name in self._checked:
            self._checked.discard(name)
        else:
            self._checked.add(name)

        check_mark = "[x]" if name in self._checked else "[ ]"
        values = self.model_tree.item(item_id, "values")
        self.model_tree.item(item_id, values=(check_mark, values[1]))
        self._update_count()

    def _filter_list(self, *args):
        text = self._search_var.get().strip().lower()
        if "," in text:
            terms = [t.strip() for t in text.split(",") if t.strip()]
        else:
            terms = [text] if text else []

        # Detach all, then re-attach matching ones
        all_items = list(self._all_models.keys())
        for name in all_items:
            try:
                self.model_tree.detach(name)
            except tk.TclError:
                pass

        for name in sorted(self._all_models.keys()):
            if not terms or any(term in name.lower() for term in terms):
                model = self._all_models.get(name)
                if model:
                    sub_date = getattr(model, "subscribed_string", None) or "N/A"
                    price = getattr(model, "final_current_price", 0) or 0
                    display = f"{name}  =>  subscribed date: {sub_date} | current_price: {price}"
                else:
                    display = name
                check_mark = "[x]" if name in self._checked else "[ ]"
                try:
                    self.model_tree.reattach(name, "", tk.END)
                    self.model_tree.item(name, values=(check_mark, display))
                except tk.TclError:
                    self.model_tree.insert("", tk.END, iid=name, values=(check_mark, display))

    def _select_all(self):
        for item_id in self.model_tree.get_children():
            self._checked.add(item_id)
            values = self.model_tree.item(item_id, "values")
            self.model_tree.item(item_id, values=("[x]", values[1]))
        self._update_count()

    def _deselect_all(self):
        for item_id in self.model_tree.get_children():
            self._checked.discard(item_id)
            values = self.model_tree.item(item_id, "values")
            self.model_tree.item(item_id, values=("[ ]", values[1]))
        self._update_count()

    def _toggle_all(self):
        for item_id in self.model_tree.get_children():
            if item_id in self._checked:
                self._checked.discard(item_id)
                mark = "[ ]"
            else:
                self._checked.add(item_id)
                mark = "[x]"
            values = self.model_tree.item(item_id, "values")
            self.model_tree.item(item_id, values=(mark, values[1]))
        self._update_count()

    def _update_count(self):
        total = len(self._all_models)
        checked = len(self._checked)
        self.count_label.configure(text=f"{checked} / {total} selected")

    def _get_selected_names(self):
        return list(self._checked)

    def reset_to_defaults(self):
        self._checked.clear()
        for item_id in self.model_tree.get_children():
            values = self.model_tree.item(item_id, "values")
            self.model_tree.item(item_id, values=("[ ]", values[1]))
        self._update_count()
        self._search_var.set("")
        self._reset_filters()

    def _apply_filters(self):
        if not self._all_models:
            return

        models = list(self._all_models.values())

        # Renewal filter
        renewal = self._renewal_var.get()
        if renewal == "Renewal On":
            models = [m for m in models if getattr(m, "renewed", False)]
        elif renewal == "Renewal Off":
            models = [m for m in models if not getattr(m, "renewed", False)]

        # Status filter
        status = self._status_var.get()
        if status == "Active Only":
            models = [m for m in models if getattr(m, "active", False)]
        elif status == "Expired Only":
            models = [m for m in models if not getattr(m, "active", False)]

        # Promo filter
        promo = self._promo_var.get()
        if promo == "Has Claimable Promo":
            models = [m for m in models if getattr(m, "lowest_promo_claim", None) is not None]
        elif promo == "No Promo":
            models = [m for m in models if getattr(m, "lowest_promo_claim", None) is None]

        # Free trial filter
        ft = self._free_trial_var.get()
        if ft == "Free Trial Only":
            models = [m for m in models
                      if getattr(m, "final_current_price", None) == 0
                      and getattr(m, "lowest_promo_claim", None) is not None]
        elif ft == "No Free Trial":
            models = [m for m in models
                      if not (getattr(m, "final_current_price", None) == 0
                              and getattr(m, "lowest_promo_claim", None) is not None)]

        # Last seen filter
        ls = self._last_seen_var.get()
        if ls == "Visible":
            models = [m for m in models if getattr(m, "last_seen", None) is not None]
        elif ls == "Hidden":
            models = [m for m in models if getattr(m, "last_seen", None) is None]

        # Price range
        min_price = self._price_min_var.get()
        max_price = self._price_max_var.get()
        if min_price > 0:
            models = [m for m in models if getattr(m, "final_current_price", 0) >= min_price]
        if max_price > 0:
            models = [m for m in models if getattr(m, "final_current_price", 0) <= max_price]

        # Sort
        sort_label = self._sort_var.get()
        sort_key = "name"
        for label, key in SORT_OPTIONS:
            if label == sort_label:
                sort_key = key
                break
        reverse = self._sort_desc_var.get()

        sort_attr_map = {
            "name": "name", "last-seen": "final_last_seen",
            "expired": "final_expired", "subscribed": "final_subscribed",
            "current-price": "final_current_price", "promo-price": "final_promo_price",
            "renewal-price": "final_renewal_price", "regular-price": "final_regular_price",
        }
        attr = sort_attr_map.get(sort_key, "name")
        try:
            models.sort(key=lambda m: getattr(m, attr, "") or "", reverse=reverse)
        except TypeError:
            models.sort(key=lambda m: str(getattr(m, attr, "")), reverse=reverse)

        names = [m.name for m in models]
        self._populate_list(names)

    def _reset_filters(self):
        self._renewal_var.set("All")
        self._status_var.set("All")
        self._promo_var.set("All")
        self._free_trial_var.set("All")
        self._last_seen_var.set("All")
        self._price_min_var.set(0)
        self._price_max_var.set(0)
        self._sort_var.set(SORT_OPTIONS[0][0])
        self._sort_desc_var.set(False)
        self._apply_filters()

    def pre_filter_username(self, username_text):
        if not username_text:
            self._search_var.set("")
            return

        usernames = [u.strip().lower() for u in username_text.split(",") if u.strip()]
        if not usernames:
            self._search_var.set("")
            return

        self._search_var.set(username_text)

        # Auto-select exact matches
        for name in self._all_models:
            if name.lower() in usernames:
                self._checked.add(name)
        self._filter_list()
        self._update_count()

    def _on_back(self):
        parent_stack = self.master
        if parent_stack and hasattr(parent_stack, "_show_page"):
            parent_stack._show_page(2)

    def _on_next(self):
        selected = self._get_selected_names()
        if not selected:
            app_signals.error_occurred.emit(
                "No Models Selected",
                "Please select at least one model to continue.",
            )
            return

        selected_models = [
            self._all_models[name] for name in selected if name in self._all_models
        ]
        log.info(f"Models selected: {len(selected_models)}")
        app_signals.models_selected.emit(selected_models)

    # Called when page becomes visible
    def on_show(self):
        if not self._all_models:
            self.populate_from_manager()
