import logging
import os
import subprocess as _subprocess
import sys as _sys
import tkinter as tk
from tkinter import ttk, messagebox

from ofscraper.gui.signals import app_signals
from ofscraper.gui.widgets.console_log import ConsoleLogWidget
from ofscraper.gui.widgets.data_table import MediaDataTable
from ofscraper.gui.widgets.progress_panel import ProgressSummaryBar
from ofscraper.gui.widgets.sidebar import FilterSidebar
from ofscraper.gui.widgets.styled_button import StyledButton

log = logging.getLogger("shared")


class TablePage(ttk.Frame):
    """Main workspace page combining data table, filter sidebar,
    console log, and progress panel. Replaces the Textual InputApp."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._scrape_active = False
        self._pending_new_scrape_nav = False
        self._pending_reset = False
        self._sidebar_visible = True
        self._setup_ui()
        self._connect_signals()

    def _reset_scrape_controls(self):
        """Reset toolbar state to a ready-to-scrape baseline."""
        try:
            self._scrape_active = False
            self.start_scraping_btn.configure(state=tk.NORMAL)
            self.start_scraping_btn.configure(text="Start Scraping >>")
        except Exception:
            pass
        try:
            self.stop_daemon_btn.pack_forget()
            self.stop_daemon_btn.configure(state=tk.NORMAL)
            self.stop_daemon_btn.configure(text="Stop Daemon")
        except Exception:
            pass
        try:
            self.daemon_status_label.pack_forget()
        except Exception:
            pass

    def _navigate_to_action_page(self):
        parent_stack = self.master
        if parent_stack and hasattr(parent_stack, "_show_page"):
            parent_stack._show_page(0)  # action page

    def _setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # main content gets the stretch

        # -- Top toolbar --
        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew")
        self._toolbar = toolbar

        # Left-side buttons
        self.toggle_sidebar_btn = StyledButton(toolbar, text="Filters",
                                                command=self._toggle_sidebar)
        self.toggle_sidebar_btn.pack(side=tk.LEFT, padx=(12, 4), pady=6)

        self.reset_btn = StyledButton(toolbar, text="Reset",
                                       command=self._on_reset)
        self.reset_btn.pack(side=tk.LEFT, padx=4, pady=6)

        self.filter_btn = StyledButton(toolbar, text="Apply Filters",
                                        primary=True, command=self._on_filter)
        self.filter_btn.pack(side=tk.LEFT, padx=4, pady=6)

        # Spacer
        ttk.Frame(toolbar, width=12).pack(side=tk.LEFT)

        self.start_scraping_btn = StyledButton(toolbar, text="Start Scraping >>",
                                                primary=True,
                                                command=self._on_start_scraping)
        self.start_scraping_btn.configure(style="Green.TButton")
        self.start_scraping_btn.pack(side=tk.LEFT, padx=4, pady=6)

        self.new_scrape_btn = StyledButton(toolbar, text="New Scrape",
                                            command=self._on_new_scrape)
        self.new_scrape_btn.configure(style="Mauve.TButton")
        self.new_scrape_btn.pack(side=tk.LEFT, padx=4, pady=6)

        self.open_folder_btn = StyledButton(toolbar, text="Open Downloads Folder",
                                             command=self._on_open_downloads_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=4, pady=6)

        # Daemon controls container — keeps pack order stable for show/hide
        self._daemon_container = ttk.Frame(toolbar)
        self._daemon_container.pack(side=tk.LEFT, padx=(4, 0))

        self.stop_daemon_btn = StyledButton(self._daemon_container,
                                             text="Stop Daemon", danger=True,
                                             command=self._on_stop_daemon)
        # Initially hidden (not packed)

        self.daemon_status_label = ttk.Label(self._daemon_container, text="",
                                              style="Muted.TLabel")
        # Initially hidden (not packed)

        # Right-side buttons (pack from right)
        self.send_btn = StyledButton(toolbar, text=">> Send Downloads",
                                      command=self._on_send_downloads)
        self.send_btn.configure(style="Peach.TButton")
        self.send_btn.pack(side=tk.RIGHT, padx=(4, 12), pady=6)

        ttk.Frame(toolbar, width=12).pack(side=tk.RIGHT)

        self.deselect_all_cart_btn = StyledButton(toolbar, text="Deselect All",
                                                   command=self._on_deselect_all_cart)
        self.deselect_all_cart_btn.pack(side=tk.RIGHT, padx=4, pady=6)

        self.select_all_cart_btn = StyledButton(toolbar, text="Select All",
                                                 command=self._on_select_all_cart)
        self.select_all_cart_btn.pack(side=tk.RIGHT, padx=4, pady=6)

        ttk.Frame(toolbar, width=8).pack(side=tk.RIGHT)

        self.cart_label = ttk.Label(toolbar, text="Cart: 0 items",
                                    style="Subheading.TLabel")
        self.cart_label.pack(side=tk.RIGHT, padx=4, pady=6)

        # -- Main content area: sidebar + table --
        self._content_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self._content_pane.grid(row=1, column=0, sticky="nsew")

        # Sidebar
        self.sidebar = FilterSidebar(self._content_pane)
        self._content_pane.add(self.sidebar, weight=0)

        # Right side: table + console (vertical pane)
        right_pane = ttk.PanedWindow(self._content_pane, orient=tk.VERTICAL)

        # Data table
        self.data_table = MediaDataTable(right_pane)
        right_pane.add(self.data_table, weight=3)

        # Console log
        self.console_widget = ConsoleLogWidget(right_pane)
        right_pane.add(self.console_widget, weight=1)

        self._content_pane.add(right_pane, weight=1)

        # -- Status bar at bottom --
        status_bar = ttk.Frame(self, style="Toolbar.TFrame")
        status_bar.grid(row=2, column=0, sticky="ew")
        self._status_bar = status_bar

        self.row_count_label = ttk.Label(status_bar, text="0 rows",
                                          style="Muted.TLabel")
        self.row_count_label.pack(side=tk.LEFT, padx=(12, 10), pady=4)

        # Overall progress embedded in the footer
        self.progress_summary = ProgressSummaryBar(status_bar)
        self.progress_summary.pack(side=tk.LEFT, fill=tk.X, expand=True,
                                    padx=(0, 10), pady=4)

        hint_label = ttk.Label(
            status_bar,
            text="Click Download_Cart cell to toggle  |  Right-click cell to filter  |  Click header to sort",
            style="Muted.TLabel",
        )
        hint_label.pack(side=tk.RIGHT, padx=(10, 12), pady=4)

    def _connect_signals(self):
        # Data table callbacks
        self.data_table._on_cart_count_changed = self._on_cart_count_changed
        self.data_table._on_cell_filter_requested = self._on_cell_filter_requested

        # App-level signals
        app_signals.scraping_finished.connect(self._on_scraping_finished)
        app_signals.daemon_next_run.connect(self._on_daemon_countdown)
        app_signals.daemon_run_starting.connect(self._on_daemon_run_starting)
        app_signals.daemon_stopped.connect(self._on_daemon_stopped)
        app_signals.theme_changed.connect(lambda _: self._apply_theme())

    def _apply_theme(self):
        """Re-apply theme colors when theme changes."""
        try:
            self.console_widget.update_theme()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Sidebar toggle
    # ------------------------------------------------------------------ #

    def _toggle_sidebar(self):
        if self._sidebar_visible:
            self._content_pane.forget(self.sidebar)
            self._sidebar_visible = False
        else:
            self._content_pane.insert(0, self.sidebar, weight=0)
            self._sidebar_visible = True

    def show_sidebar(self):
        """Ensure the sidebar is visible (called externally by main_window)."""
        if not self._sidebar_visible:
            self._toggle_sidebar()

    # ------------------------------------------------------------------ #
    #  Filter controls
    # ------------------------------------------------------------------ #

    def _on_reset(self):
        """Reset all filters and show all data."""
        self.sidebar.reset_all()
        self.data_table.reset_filter()
        self._update_row_count()

    def _on_filter(self):
        """Apply current sidebar filter state to the table."""
        state = self.sidebar.collect_state()
        self.data_table.apply_filter(state)
        self._update_row_count()

    # ------------------------------------------------------------------ #
    #  Cart controls
    # ------------------------------------------------------------------ #

    def _on_select_all_cart(self):
        self.data_table.select_all_cart()

    def _on_deselect_all_cart(self):
        self.data_table.deselect_all_cart()

    def _on_send_downloads(self):
        """Send all [added] items to the download queue."""
        cart_items = self.data_table.get_cart_items()
        if not cart_items:
            app_signals.error_occurred.emit(
                "Empty Cart",
                "No items in the download cart. Click cells in the Download Cart column to add items.",
            )
            return

        log.info(f"Sending {len(cart_items)} downloads to queue")
        app_signals.status_message.emit(
            f"Queued {len(cart_items)} downloads"
        )

        # Put items into the row queue for processing
        for row_data, row_key in cart_items:
            self.data_table.row_queue.put((row_data, row_key))

        # Emit signal for the download processor
        app_signals.downloads_queued.emit(
            [item[0] for item in cart_items]
        )

    # ------------------------------------------------------------------ #
    #  Scraping controls
    # ------------------------------------------------------------------ #

    def _on_start_scraping(self):
        """Read areas from the area page and start scraping."""
        parent_stack = self.master
        area_page = None
        if parent_stack:
            area_page = parent_stack._pages.get(2)  # index 2 = area page

        if not area_page:
            app_signals.error_occurred.emit(
                "Error", "Could not find area configuration."
            )
            return

        selected_areas = area_page.get_selected_areas()
        # Modes that don't require area selection
        _no_area_modes = {"msg_check", "paid_check", "story_check", "subscribe"}
        _current_actions = getattr(area_page, "_current_actions", set()) or set()
        _skip_area_check = bool(_current_actions & _no_area_modes)
        if not selected_areas and not _skip_area_check:
            app_signals.error_occurred.emit(
                "No Areas Selected",
                "No content areas were configured. Go back and select areas.",
            )
            return

        # New scrape run: clear table + progress UI immediately
        try:
            self.data_table.clear_all()
        except Exception:
            pass
        try:
            self.progress_summary.clear_all()
        except Exception:
            pass
        self._update_row_count()

        # Disable the button to prevent double-starts
        self.start_scraping_btn.configure(state=tk.DISABLED)
        self.start_scraping_btn.configure(text="Scraping...")
        self._scrape_active = True

        # Emit additional options from the area page
        if getattr(area_page, "_scrape_paid_var", None) and area_page._scrape_paid_var.get():
            app_signals.scrape_paid_toggled.emit(True)
        if getattr(area_page, "_scrape_labels_var", None) and area_page._scrape_labels_var.get():
            app_signals.scrape_labels_toggled.emit(True)
        # Discord webhook updates
        try:
            enabled = bool(
                getattr(area_page, "_discord_var", None)
                and area_page.discord_updates_check.instate(["!disabled"])
                and area_page._discord_var.get()
            )
            app_signals.discord_configured.emit(enabled)
        except Exception:
            pass

        # Emit advanced scrape options
        try:
            advanced = {
                "allow_dupe_downloads": bool(
                    getattr(area_page, "_allow_dupes_var", None)
                    and area_page._allow_dupes_var.get()
                ),
                "rescrape_all": bool(
                    getattr(area_page, "_rescrape_var", None)
                    and area_page._rescrape_var.get()
                ),
                "delete_model_db": bool(
                    getattr(area_page, "_delete_db_var", None)
                    and area_page._delete_db_var.get()
                ),
                "delete_downloads": bool(
                    getattr(area_page, "_delete_dl_var", None)
                    and area_page._delete_dl_var.get()
                ),
            }
            app_signals.advanced_scrape_configured.emit(advanced)
        except Exception:
            pass

        # Emit daemon configuration
        daemon_enabled = area_page.is_daemon_enabled()
        if daemon_enabled:
            app_signals.daemon_configured.emit(
                True,
                area_page.get_daemon_interval(),
                area_page.is_notify_enabled(),
                area_page.is_sound_enabled(),
            )
            self.stop_daemon_btn.pack(side=tk.LEFT, padx=(0, 8))
            self.daemon_status_label.configure(text="Daemon mode active")
            self.daemon_status_label.pack(side=tk.LEFT)
        else:
            app_signals.daemon_configured.emit(False, 30.0, False, False)

        # Emit date range from the filter sidebar
        try:
            fs = getattr(area_page, "filter_sidebar", None)
            if fs is not None:
                date_enabled = bool(
                    getattr(fs, "date_enabled", None)
                    and fs.date_enabled.isChecked()
                )
                from_date = (
                    fs.min_date.date().toString("yyyy-MM-dd")
                    if date_enabled and getattr(fs, "min_date", None)
                    else None
                )
                to_date = (
                    fs.max_date.date().toString("yyyy-MM-dd")
                    if date_enabled and getattr(fs, "max_date", None)
                    else None
                )
                app_signals.date_range_configured.emit(
                    {"enabled": date_enabled, "from_date": from_date, "to_date": to_date}
                )
        except Exception:
            pass

        log.info(f"Starting scrape with areas: {selected_areas}")
        app_signals.areas_selected.emit(selected_areas)

    # ------------------------------------------------------------------ #
    #  Scraping lifecycle callbacks
    # ------------------------------------------------------------------ #

    def _on_scraping_finished(self):
        """Re-enable the Start Scraping button when scraping completes."""
        self._scrape_active = False
        if self._pending_new_scrape_nav:
            self._pending_new_scrape_nav = False
            if self._pending_reset:
                self._pending_reset = False
                self._reset_all_pages()
            self._reset_scrape_controls()
            self._navigate_to_action_page()
            return
        if self.stop_daemon_btn.winfo_ismapped():
            self.start_scraping_btn.configure(text="Daemon waiting...")
            return
        self.start_scraping_btn.configure(state=tk.NORMAL)
        self.start_scraping_btn.configure(text="Start Scraping >>")
        self.daemon_status_label.pack_forget()

    def _on_daemon_countdown(self, text):
        """Update the daemon countdown label with remaining time."""
        self.daemon_status_label.configure(text=text)
        if not self.daemon_status_label.winfo_ismapped():
            self.daemon_status_label.pack(side=tk.LEFT)

    def _on_daemon_run_starting(self, run_number):
        """Update UI when a daemon re-run begins."""
        self._scrape_active = True
        try:
            self.data_table.clear_all()
        except Exception:
            pass
        try:
            self.progress_summary.clear_all()
        except Exception:
            pass
        self._update_row_count()
        self.start_scraping_btn.configure(text=f"Scraping (run #{run_number})...")
        self.daemon_status_label.configure(text=f"Daemon run #{run_number}")
        if not self.daemon_status_label.winfo_ismapped():
            self.daemon_status_label.pack(side=tk.LEFT)

    def _on_daemon_stopped(self):
        """Reset UI when daemon mode is stopped."""
        self.stop_daemon_btn.pack_forget()
        self.daemon_status_label.pack_forget()
        self.start_scraping_btn.configure(state=tk.NORMAL)
        self.start_scraping_btn.configure(text="Start Scraping >>")
        self._scrape_active = False

    def _on_stop_daemon(self):
        """Request the daemon loop to stop."""
        app_signals.stop_daemon_requested.emit()
        self.stop_daemon_btn.configure(state=tk.DISABLED)
        self.stop_daemon_btn.configure(text="Stopping...")
        self.daemon_status_label.configure(text="Stopping daemon...")

    # ------------------------------------------------------------------ #
    #  New scrape / reset
    # ------------------------------------------------------------------ #

    def _ask_reset_options(self):
        """Ask whether to reset all scrape options/models to defaults."""
        return messagebox.askyesno(
            "Reset options?",
            "Do you want to reset all scrape options and selected models\n"
            "back to their defaults?\n\n"
            "Yes = start fresh (like opening the GUI for the first time)\n"
            "No = keep your current selections",
        )

    def _reset_all_pages(self):
        """Reset action, area, and model pages to their defaults."""
        parent_stack = self.master
        if not parent_stack:
            return
        for idx in (0, 1, 2):  # action, area, model pages
            page = parent_stack._pages.get(idx)
            if page and hasattr(page, "reset_to_defaults"):
                try:
                    page.reset_to_defaults()
                except Exception:
                    pass

    def _on_open_downloads_folder(self):
        """Open the configured save_location in the system file manager."""
        try:
            from ofscraper.utils.config.file import open_config
            config = open_config()
            folder = config.get("file_options", {}).get("save_location", "")
            if not folder:
                folder = config.get("save_location", "")
        except Exception:
            folder = ""

        if not folder:
            messagebox.showwarning(
                "No Download Folder",
                "No save location is configured.\n"
                "Set one in Configuration \u2192 File Options \u2192 Save Location.",
            )
            return

        folder = os.path.expandvars(os.path.expanduser(folder))
        if not os.path.isdir(folder):
            messagebox.showwarning(
                "Folder Not Found",
                f"The configured download folder does not exist:\n{folder}",
            )
            return

        # Open in system file manager
        if _sys.platform == "win32":
            os.startfile(folder)
        elif _sys.platform == "darwin":
            _subprocess.Popen(["open", folder])
        else:
            _subprocess.Popen(["xdg-open", folder])

    def _on_new_scrape(self):
        """Navigate back to the action page to start a new scrape."""
        if self._scrape_active:
            if not messagebox.askyesno(
                "Cancel current scrape?",
                "Content is currently being scraped.\n\n"
                "Cancel the current scrape and return to the beginning?",
            ):
                return
            self._pending_reset = self._ask_reset_options()
            try:
                app_signals.cancel_scrape_requested.emit()
            except Exception:
                pass
            self._pending_new_scrape_nav = True
            try:
                self.start_scraping_btn.configure(text="Cancelling...")
                self.start_scraping_btn.configure(state=tk.DISABLED)
            except Exception:
                pass
            try:
                self.daemon_status_label.configure(text="Cancelling current scrape...")
                if not self.daemon_status_label.winfo_ismapped():
                    self.daemon_status_label.pack(side=tk.LEFT)
            except Exception:
                pass
            return

        # If daemon mode is active, stop it
        try:
            if self.stop_daemon_btn.winfo_ismapped():
                app_signals.stop_daemon_requested.emit()
        except Exception:
            pass

        if self._ask_reset_options():
            self._reset_all_pages()

        self._reset_scrape_controls()
        self._navigate_to_action_page()

    # ------------------------------------------------------------------ #
    #  Table event handlers
    # ------------------------------------------------------------------ #

    def _on_cart_count_changed(self, count):
        self.cart_label.configure(text=f"Cart: {count} items")

    def _on_cell_filter_requested(self, col_name, value):
        """When user right-clicks a cell to filter by that value."""
        self.sidebar.update_field(col_name, value)
        self._on_filter()

    def _update_row_count(self):
        count = len(self.data_table._display_data)
        total = len(self.data_table._raw_data)
        if count == total:
            self.row_count_label.configure(text=f"{count} rows")
        else:
            self.row_count_label.configure(text=f"{count} / {total} rows (filtered)")

    # ------------------------------------------------------------------ #
    #  Data loading
    # ------------------------------------------------------------------ #

    def load_data(self, table_data):
        """Load table data from the scraper pipeline (replaces existing)."""
        if not table_data:
            return
        if isinstance(table_data[0], dict):
            self.data_table.load_data(table_data)
        else:
            self.data_table.load_data(table_data[1:])
        self._update_row_count()
        app_signals.status_message.emit(
            f"Loaded {len(self.data_table._raw_data)} items"
        )

    def append_data(self, table_data):
        """Append new rows to the table (for incremental per-user updates)."""
        if not table_data:
            return
        self.data_table.append_data(table_data)
        self._update_row_count()
        app_signals.status_message.emit(
            f"{len(self.data_table._raw_data)} total items"
        )
