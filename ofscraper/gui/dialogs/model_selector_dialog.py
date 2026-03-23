"""Modal dialog for selecting models/creators before scraping starts."""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ofscraper.gui.styles import c
from ofscraper.gui.widgets.styled_button import StyledButton

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

_CHECK_ON = "[x]"
_CHECK_OFF = "[ ]"


class ModelSelectorDialog(tk.Toplevel):
    """Modal dialog for model/creator selection.
    Shows the loaded model list, allows search/filter/sort, returns selected models."""

    def __init__(self, all_models, parent=None):
        super().__init__(parent)
        self._all_models = all_models  # dict: name -> model object
        self._selected_models = []
        self._checked = set()  # set of model names that are checked
        self._items = {}  # iid -> model name mapping

        self.title("Select Models")
        self.minsize(900, 600)
        self.geometry("1000x650")

        # Make modal
        if parent:
            self.transient(parent)
        self.grab_set()

        self._setup_ui()

        # Center on parent
        self.update_idletasks()
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
            y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        header = ttk.Label(main_frame, text="Select Models to Scrape",
                           font=("Segoe UI", 18, "bold"))
        header.pack(anchor="w")

        subtitle = ttk.Label(main_frame,
                             text="Search and select the creators you want to process.",
                             foreground=c("subtext"))
        subtitle.pack(anchor="w", pady=(4, 12))

        # Main content: PanedWindow with list on left, filters on right
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # -- Left: search + model list --
        left_frame = self._build_left_panel(paned)
        paned.add(left_frame, weight=3)

        # -- Right: filter panel --
        right_frame = self._build_right_panel(paned)
        paned.add(right_frame, weight=1)

        # Bottom buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(12, 0))

        spacer = ttk.Frame(btn_frame)
        spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)

        cancel_btn = StyledButton(btn_frame, text="Cancel",
                                  command=self._on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.ok_btn = StyledButton(btn_frame, text="Start Scraping >>",
                                   primary=True, command=self._on_ok)
        self.ok_btn.pack(side=tk.LEFT)

        # Populate list
        self._populate_list(sorted(self._all_models.keys()))

    def _build_left_panel(self, parent):
        frame = ttk.Frame(parent)

        # Search bar
        self.search_input = ttk.Entry(frame)
        self.search_input.pack(fill=tk.X, pady=(0, 8))

        # Bind search on key release
        self.search_input.bind("<KeyRelease>", lambda e: self._filter_list())

        # Bulk action buttons
        bulk_frame = ttk.Frame(frame)
        bulk_frame.pack(fill=tk.X, pady=(0, 8))

        select_all_btn = ttk.Button(bulk_frame, text="Select All",
                                    command=self._select_all)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 4))

        deselect_all_btn = ttk.Button(bulk_frame, text="Deselect All",
                                      command=self._deselect_all)
        deselect_all_btn.pack(side=tk.LEFT, padx=(0, 4))

        toggle_btn = ttk.Button(bulk_frame, text="Toggle",
                                command=self._toggle_all)
        toggle_btn.pack(side=tk.LEFT, padx=(0, 4))

        spacer = ttk.Frame(bulk_frame)
        spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.count_label = ttk.Label(bulk_frame, text="0 / 0 selected",
                                     foreground=c("subtext"))
        self.count_label.pack(side=tk.RIGHT)

        # Model treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.model_tree = ttk.Treeview(
            tree_frame,
            columns=("check", "display"),
            show="headings",
            selectmode="browse",
        )
        self.model_tree.heading("check", text="")
        self.model_tree.heading("display", text="Model")
        self.model_tree.column("check", width=40, minwidth=40, stretch=False, anchor="center")
        self.model_tree.column("display", width=500, minwidth=200, stretch=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                    command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=tree_scroll.set)

        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Click handler to toggle check
        self.model_tree.bind("<ButtonRelease-1>", self._on_tree_click)

        return frame

    def _build_right_panel(self, parent):
        frame = ttk.Frame(parent)
        frame.configure(width=300)

        inner = ttk.Frame(frame)
        inner.pack(fill=tk.BOTH, expand=True, padx=(8, 0))

        filter_label = ttk.Label(inner, text="Filters",
                                 font=("Segoe UI", 14, "bold"))
        filter_label.pack(anchor="w", pady=(0, 8))

        # Subscription type
        sub_group = ttk.LabelFrame(inner, text="Subscription Type")
        sub_group.pack(fill=tk.X, pady=(0, 8))

        sub_inner = ttk.Frame(sub_group)
        sub_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(sub_inner, text="Renewal:").grid(row=0, column=0, sticky="w", pady=2)
        self.renewal_var = tk.StringVar(value="All")
        self.renewal_combo = ttk.Combobox(sub_inner, textvariable=self.renewal_var,
                                          values=["All", "Renewal On", "Renewal Off"],
                                          state="readonly", width=16)
        self.renewal_combo.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        ttk.Label(sub_inner, text="Status:").grid(row=1, column=0, sticky="w", pady=2)
        self.status_var = tk.StringVar(value="All")
        self.status_combo = ttk.Combobox(sub_inner, textvariable=self.status_var,
                                         values=["All", "Active Only", "Expired Only"],
                                         state="readonly", width=16)
        self.status_combo.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=2)

        sub_inner.columnconfigure(1, weight=1)

        # Price range
        price_group = ttk.LabelFrame(inner, text="Price Range")
        price_group.pack(fill=tk.X, pady=(0, 8))

        price_inner = ttk.Frame(price_group)
        price_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(price_inner, text="Min:").grid(row=0, column=0, sticky="w", pady=2)
        self.price_min_var = tk.DoubleVar(value=0.0)
        self.price_min = ttk.Spinbox(price_inner, from_=0, to=99999,
                                     textvariable=self.price_min_var,
                                     increment=1.0, width=12)
        self.price_min.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        ttk.Label(price_inner, text="Max:").grid(row=1, column=0, sticky="w", pady=2)
        self.price_max_var = tk.DoubleVar(value=0.0)
        self.price_max = ttk.Spinbox(price_inner, from_=0, to=99999,
                                     textvariable=self.price_max_var,
                                     increment=1.0, width=12)
        self.price_max.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=2)

        price_inner.columnconfigure(1, weight=1)

        # Sort
        sort_group = ttk.LabelFrame(inner, text="Sort")
        sort_group.pack(fill=tk.X, pady=(0, 8))

        sort_inner = ttk.Frame(sort_group)
        sort_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(sort_inner, text="Sort by:").grid(row=0, column=0, sticky="w", pady=2)
        self.sort_var = tk.StringVar(value=SORT_OPTIONS[0][0])
        self.sort_combo = ttk.Combobox(sort_inner, textvariable=self.sort_var,
                                       values=[label for label, _ in SORT_OPTIONS],
                                       state="readonly", width=16)
        self.sort_combo.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        self.sort_desc_var = tk.BooleanVar(value=False)
        self.sort_desc_check = ttk.Checkbutton(sort_inner, text="Descending",
                                                variable=self.sort_desc_var)
        self.sort_desc_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)

        sort_inner.columnconfigure(1, weight=1)

        # Apply button
        apply_btn = StyledButton(inner, text="Apply Filters", primary=True,
                                 command=self._apply_filters)
        apply_btn.pack(fill=tk.X, pady=(4, 0))

        return frame

    def _populate_list(self, names):
        """Populate the treeview with model names."""
        # Clear existing items
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
        self._items.clear()

        for name in names:
            model = self._all_models.get(name)
            if model:
                sub_date = getattr(model, "subscribed_string", None) or "N/A"
                price = getattr(model, "final_current_price", 0) or 0
                display = f"{name}  =>  subscribed: {sub_date} | price: {price}"
            else:
                display = name

            check_mark = _CHECK_ON if name in self._checked else _CHECK_OFF
            iid = self.model_tree.insert("", tk.END, values=(check_mark, display))
            self._items[iid] = name

        self._update_count()

    def _on_tree_click(self, event):
        """Toggle check state when a row is clicked."""
        region = self.model_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        iid = self.model_tree.identify_row(event.y)
        if not iid or iid not in self._items:
            return

        name = self._items[iid]
        if name in self._checked:
            self._checked.discard(name)
            self.model_tree.set(iid, "check", _CHECK_OFF)
        else:
            self._checked.add(name)
            self.model_tree.set(iid, "check", _CHECK_ON)

        self._update_count()

    def _filter_list(self):
        """Filter treeview items based on search text."""
        text_lower = self.search_input.get().lower()
        # We need to show/hide items -- Treeview doesn't support hiding natively,
        # so we detach/reattach items
        for iid in list(self._items.keys()):
            values = self.model_tree.item(iid, "values")
            if values and len(values) > 1:
                display = str(values[1]).lower()
                if text_lower in display:
                    try:
                        self.model_tree.reattach(iid, "", tk.END)
                    except Exception:
                        pass
                else:
                    self.model_tree.detach(iid)
            elif not text_lower:
                try:
                    self.model_tree.reattach(iid, "", tk.END)
                except Exception:
                    pass

    def _get_visible_iids(self):
        """Return IIDs of items currently visible in the tree."""
        return list(self.model_tree.get_children())

    def _select_all(self):
        for iid in self._get_visible_iids():
            name = self._items.get(iid)
            if name:
                self._checked.add(name)
                self.model_tree.set(iid, "check", _CHECK_ON)
        self._update_count()

    def _deselect_all(self):
        for iid in self._get_visible_iids():
            name = self._items.get(iid)
            if name:
                self._checked.discard(name)
                self.model_tree.set(iid, "check", _CHECK_OFF)
        self._update_count()

    def _toggle_all(self):
        for iid in self._get_visible_iids():
            name = self._items.get(iid)
            if name:
                if name in self._checked:
                    self._checked.discard(name)
                    self.model_tree.set(iid, "check", _CHECK_OFF)
                else:
                    self._checked.add(name)
                    self.model_tree.set(iid, "check", _CHECK_ON)
        self._update_count()

    def _update_count(self):
        checked = len(self._checked)
        total = len(self._items)
        self.count_label.configure(text=f"{checked} / {total} selected")

    def _get_selected_names(self):
        return list(self._checked)

    def _apply_filters(self):
        if not self._all_models:
            return

        models = list(self._all_models.values())

        # Renewal filter
        renewal = self.renewal_var.get()
        if renewal == "Renewal On":
            models = [m for m in models if getattr(m, "renewed", False)]
        elif renewal == "Renewal Off":
            models = [m for m in models if not getattr(m, "renewed", False)]

        # Status filter
        status = self.status_var.get()
        if status == "Active Only":
            models = [m for m in models if getattr(m, "active", False)]
        elif status == "Expired Only":
            models = [m for m in models if not getattr(m, "active", False)]

        # Price range
        min_price = self.price_min_var.get()
        max_price = self.price_max_var.get()
        if min_price > 0:
            models = [m for m in models if getattr(m, "final_current_price", 0) >= min_price]
        if max_price > 0:
            models = [m for m in models if getattr(m, "final_current_price", 0) <= max_price]

        # Sort
        sort_label = self.sort_var.get()
        sort_key = "name"
        for label, key in SORT_OPTIONS:
            if label == sort_label:
                sort_key = key
                break
        reverse = self.sort_desc_var.get()

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

        # Rebuild list preserving checked state
        names = [m.name for m in models]
        self._populate_list(names)

    def _on_ok(self):
        selected_names = self._get_selected_names()
        if not selected_names:
            messagebox.showwarning(
                "No Models Selected",
                "Please select at least one model to continue.",
                parent=self,
            )
            return
        self._selected_models = [
            self._all_models[name]
            for name in selected_names
            if name in self._all_models
        ]
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self._selected_models = []
        self.grab_release()
        self.destroy()

    def get_selected_models(self):
        """Return the list of selected model objects after dialog is closed."""
        return self._selected_models
