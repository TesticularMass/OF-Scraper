import logging
import queue
import tkinter as tk
from tkinter import ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c

log = logging.getLogger("shared")

# Column definitions matching the TUI's ROW_NAMES
COLUMNS = [
    "Number",
    "Download_Cart",
    "UserName",
    "Downloaded",
    "Unlocked",
    "other_posts_with_media",
    "Length",
    "Mediatype",
    "Post_Date",
    "Post_Media_Count",
    "Responsetype",
    "Price",
    "Liked",
    "Post_ID",
    "Media_ID",
    "Text",
]

CART_STATES = ["[]", "[added]", "[downloading]", "[downloaded]", "[failed]"]


def _cart_color(key):
    """Get cart/status color for the current theme."""
    _MAP = {
        "[]": "muted",
        "[added]": "green",
        "[downloading]": "yellow",
        "[downloaded]": "blue",
        "[failed]": "red",
        "Locked": "surface2",
        "Preview": "sky",
        "Included": "teal",
    }
    name = _MAP.get(key)
    return c(name) if name else c("text")


class MediaDataTable(ttk.Frame):
    """ttk.Treeview-based table for displaying media data — replaces the
    PyQt6 QTableWidget / Textual DataTable.

    Supports sorting, download cart toggling, right-click filter-by-cell,
    and communicates with the download queue via the app_signals hub.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._raw_data = []       # list of dicts (original row data)
        self._display_data = []   # filtered subset
        self._row_queue = queue.Queue()
        self._sort_column = 0
        self._sort_ascending = True

        # Callback attributes — external code can set these to receive events.
        # cart_count_changed(count: int)
        self._on_cart_count_changed = None
        # cell_filter_requested(column_name: str, cell_value: str)
        self._on_cell_filter_requested = None

        self._setup_ui()
        self._connect_internal()

    # ------------------------------------------------------------------ #
    #  UI setup
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        # Column identifiers (internal names)
        col_ids = [col.lower() for col in COLUMNS]

        # Create Treeview
        self._tree = ttk.Treeview(
            self,
            columns=col_ids,
            show="headings",
            selectmode="browse",
        )

        # Define headings and column widths
        for idx, col in enumerate(COLUMNS):
            col_id = col_ids[idx]
            heading_text = col.replace("_", " ")
            self._tree.heading(
                col_id,
                text=heading_text,
                command=lambda _idx=idx: self._on_header_clicked(_idx),
            )

            # Set column widths
            if col == "Text":
                width = 300
            elif col in ("Download_Cart", "Number"):
                width = 100
            else:
                width = 120

            self._tree.column(col_id, width=width, minwidth=60, stretch=(col == "Text"))

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure row tags for alternating colors and cell-level coloring.
        # Alternating row tags are applied in _rebuild_table.
        self._tree.tag_configure("evenrow", background=c("base"))
        self._tree.tag_configure("oddrow", background=c("mantle"))

        # Cart / status color tags
        for state in CART_STATES:
            tag = f"cart_{state}"
            self._tree.tag_configure(tag, foreground=_cart_color(state))
        self._tree.tag_configure("cart_Locked", foreground=_cart_color("Locked"))

        # Downloaded column tags
        self._tree.tag_configure("dl_true", foreground=c("green"))
        self._tree.tag_configure("dl_na", foreground=c("surface2"))
        self._tree.tag_configure("dl_false", foreground=c("red"))

        # Unlocked column tags
        self._tree.tag_configure("ul_locked", foreground=c("surface2"))
        self._tree.tag_configure("ul_preview", foreground=c("sky"))
        self._tree.tag_configure("ul_included", foreground=c("teal"))
        self._tree.tag_configure("ul_true", foreground=c("green"))
        self._tree.tag_configure("ul_false", foreground=c("red"))

        # Price column tag
        self._tree.tag_configure("price_paid", foreground=c("peach"))

        # Liked column tags
        self._tree.tag_configure("liked_liked", foreground=c("green"))
        self._tree.tag_configure("liked_unliked", foreground=c("peach"))
        self._tree.tag_configure("liked_failed", foreground=c("red"))

    def _connect_internal(self):
        self._tree.bind("<ButtonRelease-1>", self._on_row_clicked)
        self._tree.bind("<Button-3>", self._on_context_menu)
        app_signals.cell_update.connect(self._on_external_cell_update)
        app_signals.posts_liked_updated.connect(self._on_posts_liked_updated)
        app_signals.theme_changed.connect(lambda _: self._refresh_tags_and_rebuild())

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    @property
    def row_queue(self):
        return self._row_queue

    def load_data(self, table_data):
        """Load raw table data (list of dicts) into the table, replacing existing data."""
        self._raw_data = table_data
        self._display_data = list(table_data)
        self._rebuild_table()

    def clear_all(self):
        """Clear all table data and reset internal state for a new scrape run."""
        self._raw_data = []
        self._display_data = []

        # Clear any queued download rows from a prior run (best-effort).
        try:
            while True:
                self._row_queue.get_nowait()
        except Exception:
            pass

        self._tree.delete(*self._tree.get_children())
        self._update_cart_count()

    def append_data(self, new_rows):
        """Append new rows to existing data (for incremental per-user updates).
        Deduplicates by media_id to prevent duplicate entries when loading
        from both the live scraper pipeline and the DB fallback."""
        def _row_identity(r):
            return (
                str(r.get("username", "")),
                str(r.get("media_id", "")),
                str(r.get("post_id", "")),
                str(r.get("responsetype", "")),
            )

        existing = {_row_identity(r) for r in self._raw_data}
        deduped = [r for r in new_rows if _row_identity(r) not in existing]
        if not deduped:
            return
        start_index = len(self._raw_data)
        for i, row in enumerate(deduped):
            row["index"] = start_index + i
        self._raw_data.extend(deduped)
        self._display_data.extend(deduped)
        self._rebuild_table()

    def apply_filter(self, filter_state):
        """Apply the filter state and rebuild the table with filtered data."""
        filtered = []
        for row in self._raw_data:
            passes = True
            for col in COLUMNS:
                col_lower = col.lower()
                if col_lower in ("number", "download_cart"):
                    continue
                val = row.get(col_lower, row.get(col, ""))
                if not filter_state.validate(col_lower, val):
                    passes = False
                    break
            if passes:
                filtered.append(row)
        self._display_data = filtered
        self._rebuild_table()

    def reset_filter(self):
        """Reset to show all data."""
        self._display_data = list(self._raw_data)
        self._rebuild_table()

    def select_all_cart(self):
        """Add all visible unlocked items to cart."""
        for row_idx, row_data in enumerate(self._display_data):
            cart_val = str(row_data.get("download_cart", row_data.get("Download_Cart", "")))
            if cart_val == "[]":
                row_data["download_cart"] = "[added]"
                # Also update in _raw_data
                idx = row_data.get("index", row_idx)
                for rd in self._raw_data:
                    if rd.get("index") == idx:
                        rd["download_cart"] = "[added]"
                        break
        self._rebuild_table()
        self._update_cart_count()

    def deselect_all_cart(self):
        """Remove all items from cart."""
        for row_idx, row_data in enumerate(self._display_data):
            cart_val = str(row_data.get("download_cart", row_data.get("Download_Cart", "")))
            if cart_val == "[added]":
                row_data["download_cart"] = "[]"
                idx = row_data.get("index", row_idx)
                for rd in self._raw_data:
                    if rd.get("index") == idx:
                        rd["download_cart"] = "[]"
                        break
        self._rebuild_table()
        self._update_cart_count()

    def get_cart_items(self):
        """Return list of (row_data, row_key) for all [added] items."""
        result = []
        for row_idx, row_data in enumerate(self._display_data):
            cart_val = str(row_data.get("download_cart", row_data.get("Download_Cart", "")))
            if cart_val == "[added]":
                row_key = str(row_data.get("index", row_idx))
                result.append((row_data, row_key))
                # Mark as downloading
                row_data["download_cart"] = "[downloading]"
                idx = row_data.get("index", row_idx)
                for rd in self._raw_data:
                    if rd.get("index") == idx:
                        rd["download_cart"] = "[downloading]"
                        break
        self._rebuild_table()
        self._update_cart_count()
        return result

    # ------------------------------------------------------------------ #
    #  Internal — rebuild / display
    # ------------------------------------------------------------------ #

    def _rebuild_table(self):
        """Clear and repopulate the Treeview from _display_data."""
        self._tree.delete(*self._tree.get_children())

        col_ids = [col.lower() for col in COLUMNS]

        for row_idx, row_data in enumerate(self._display_data):
            values = []
            for col_name in COLUMNS:
                col_lower = col_name.lower()
                if col_lower == "number":
                    value = str(row_idx + 1)
                else:
                    value = row_data.get(col_lower, row_data.get(col_name, ""))

                # Format display value
                if isinstance(value, list):
                    display = str(len(value))
                elif isinstance(value, bool):
                    display = str(value)
                else:
                    display = str(value)

                # Truncate long text
                if col_lower == "text" and len(display) > 80:
                    display = display[:80] + "..."

                values.append(display)

            # Determine the primary tag for the row (for coloring).
            # Treeview applies the *last* matching tag's config, so we use
            # a single row-level tag for the dominant color and rely on
            # the alternating-row background being set via separate tags.
            tags = self._compute_row_tags(row_idx, row_data, values)

            self._tree.insert(
                "",
                tk.END,
                iid=str(row_idx),
                values=values,
                tags=tags,
            )

        self._update_cart_count()

    def _compute_row_tags(self, row_idx, row_data, values):
        """Return a tuple of tags to apply to a row.

        Treeview does not support per-cell coloring natively.  We pick the
        most visually important column to color the entire row:
          1. download_cart status (if not the default ``[]``)
          2. downloaded status
          3. alternating row stripe
        """
        tags = []

        # Alternating row background
        tags.append("evenrow" if row_idx % 2 == 0 else "oddrow")

        # Cart column value
        cart_idx = COLUMNS.index("Download_Cart")
        cart_val = values[cart_idx] if cart_idx < len(values) else "[]"

        if cart_val in ("[added]", "[downloading]", "[downloaded]", "[failed]"):
            tags.append(f"cart_{cart_val}")
        elif cart_val == "Locked":
            tags.append("cart_Locked")
        else:
            # Use downloaded / unlocked / liked coloring for the row
            dl_idx = COLUMNS.index("Downloaded")
            dl_val = values[dl_idx] if dl_idx < len(values) else ""
            if dl_val == "True":
                tags.append("dl_true")
            elif dl_val == "N/A":
                tags.append("dl_na")
            elif dl_val == "False":
                tags.append("dl_false")

            ul_idx = COLUMNS.index("Unlocked")
            ul_val = values[ul_idx] if ul_idx < len(values) else ""
            if ul_val == "Locked":
                tags.append("ul_locked")
            elif ul_val == "Preview":
                tags.append("ul_preview")
            elif ul_val == "Included":
                tags.append("ul_included")

            liked_idx = COLUMNS.index("Liked")
            liked_val = values[liked_idx] if liked_idx < len(values) else ""
            if liked_val == "Liked":
                tags.append("liked_liked")
            elif liked_val == "Unliked":
                tags.append("liked_unliked")
            elif liked_val == "Failed":
                tags.append("liked_failed")

            price_idx = COLUMNS.index("Price")
            price_val = values[price_idx] if price_idx < len(values) else ""
            if price_val not in ("Free", "0", ""):
                tags.append("price_paid")

        return tuple(tags)

    def _refresh_tags_and_rebuild(self):
        """Re-configure tag colors (after theme change) and rebuild."""
        self._tree.tag_configure("evenrow", background=c("base"))
        self._tree.tag_configure("oddrow", background=c("mantle"))

        for state in CART_STATES:
            self._tree.tag_configure(f"cart_{state}", foreground=_cart_color(state))
        self._tree.tag_configure("cart_Locked", foreground=_cart_color("Locked"))

        self._tree.tag_configure("dl_true", foreground=c("green"))
        self._tree.tag_configure("dl_na", foreground=c("surface2"))
        self._tree.tag_configure("dl_false", foreground=c("red"))

        self._tree.tag_configure("ul_locked", foreground=c("surface2"))
        self._tree.tag_configure("ul_preview", foreground=c("sky"))
        self._tree.tag_configure("ul_included", foreground=c("teal"))
        self._tree.tag_configure("ul_true", foreground=c("green"))
        self._tree.tag_configure("ul_false", foreground=c("red"))

        self._tree.tag_configure("price_paid", foreground=c("peach"))

        self._tree.tag_configure("liked_liked", foreground=c("green"))
        self._tree.tag_configure("liked_unliked", foreground=c("peach"))
        self._tree.tag_configure("liked_failed", foreground=c("red"))

        self._rebuild_table()

    # ------------------------------------------------------------------ #
    #  Sorting
    # ------------------------------------------------------------------ #

    def _on_header_clicked(self, logical_index):
        """Sort by clicked column header."""
        if logical_index == self._sort_column:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = logical_index
            self._sort_ascending = True

        col_name = COLUMNS[logical_index].lower()
        reverse = not self._sort_ascending

        def sort_key(row):
            val = row.get(col_name, row.get(COLUMNS[logical_index], ""))
            if isinstance(val, bool):
                return (1 if val else 0,)
            if isinstance(val, list):
                return (len(val),)
            if col_name == "price":
                try:
                    return (0.0 if str(val).lower() == "free" else float(val),)
                except (ValueError, TypeError):
                    return (0.0,)
            if col_name == "number":
                try:
                    return (int(val),)
                except (ValueError, TypeError):
                    return (0,)
            try:
                return (float(val),)
            except (ValueError, TypeError):
                return (str(val).lower(),)

        try:
            self._display_data.sort(key=sort_key, reverse=reverse)
        except TypeError:
            self._display_data.sort(
                key=lambda r: str(
                    r.get(col_name, r.get(COLUMNS[logical_index], ""))
                ).lower(),
                reverse=reverse,
            )
        self._rebuild_table()

    # ------------------------------------------------------------------ #
    #  Click handlers
    # ------------------------------------------------------------------ #

    def _on_row_clicked(self, event):
        """Handle left-click — toggle download cart if the Download_Cart column was clicked."""
        region = self._tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col_id = self._tree.identify_column(event.x)
        # col_id is like "#1", "#2", etc. (1-indexed)
        try:
            col_idx = int(col_id.replace("#", "")) - 1
        except (ValueError, TypeError):
            return

        if col_idx != COLUMNS.index("Download_Cart"):
            return

        item_id = self._tree.identify_row(event.y)
        if not item_id:
            return

        try:
            row_idx = int(item_id)
        except (ValueError, TypeError):
            return

        if row_idx >= len(self._display_data):
            return

        row_data = self._display_data[row_idx]
        current = str(row_data.get("download_cart", row_data.get("Download_Cart", "")))

        if current == "Locked":
            return
        elif current == "[]":
            new_val = "[added]"
        elif current == "[added]":
            new_val = "[]"
        elif current in ("[downloaded]", "[failed]"):
            new_val = "[]"
        else:
            return

        # Update backing data
        row_data["download_cart"] = new_val
        idx = row_data.get("index", row_idx)
        for rd in self._raw_data:
            if rd.get("index") == idx:
                rd["download_cart"] = new_val
                break

        # Update the visible row in-place
        values = list(self._tree.item(item_id, "values"))
        cart_col_idx = COLUMNS.index("Download_Cart")
        values[cart_col_idx] = new_val
        tags = self._compute_row_tags(row_idx, row_data, values)
        self._tree.item(item_id, values=values, tags=tags)

        self._update_cart_count()

    def _on_context_menu(self, event):
        """Right-click context menu to filter by cell value."""
        item_id = self._tree.identify_row(event.y)
        if not item_id:
            return

        col_id = self._tree.identify_column(event.x)
        try:
            col_idx = int(col_id.replace("#", "")) - 1
        except (ValueError, TypeError):
            return

        if col_idx < 0 or col_idx >= len(COLUMNS):
            return

        col_name = COLUMNS[col_idx]
        values = self._tree.item(item_id, "values")
        if col_idx >= len(values):
            return
        value = values[col_idx]

        menu = tk.Menu(self._tree, tearoff=0)
        menu.add_command(
            label=f'Filter by "{value}"',
            command=lambda: self._emit_cell_filter(col_name, value),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _emit_cell_filter(self, col_name, value):
        """Emit the cell filter request via callback and/or signal."""
        if self._on_cell_filter_requested is not None:
            try:
                self._on_cell_filter_requested(col_name, value)
            except Exception as e:
                log.debug(f"cell_filter_requested callback error: {e}")

    # ------------------------------------------------------------------ #
    #  External update handlers
    # ------------------------------------------------------------------ #

    def _on_external_cell_update(self, row_key, column_name, new_value):
        """Handle cell updates from external sources (e.g., download completion).
        row_key matches against media_id (preferred) or index."""
        col_lower = column_name.lower()
        try:
            col_idx = [col.lower() for col in COLUMNS].index(col_lower)
        except ValueError:
            return

        for row_idx, row_data in enumerate(self._display_data):
            if str(row_data.get("media_id", "")) == row_key or str(
                row_data.get("index", "")
            ) == row_key:
                # Update backing data
                row_data[col_lower] = new_value

                # Update the visible row
                item_id = str(row_idx)
                try:
                    values = list(self._tree.item(item_id, "values"))
                    values[col_idx] = new_value
                    tags = self._compute_row_tags(row_idx, row_data, values)
                    self._tree.item(item_id, values=values, tags=tags)
                except tk.TclError:
                    pass

                if str(row_data.get("index", "")) == row_key:
                    break

    def _on_posts_liked_updated(self, results):
        """Handle posts_liked_updated signal from a like/unlike action.
        results is {post_id (int): status_str} where status_str is one of
        'Liked', 'Unliked', or 'Failed'.  Updates the Liked column for every
        media row that shares a matching post_id."""
        if not results:
            return

        liked_col_idx = COLUMNS.index("Liked")
        str_results = {str(k): v for k, v in results.items()}

        # Update _raw_data backing store
        for row in self._raw_data:
            pid = str(row.get("post_id", ""))
            if pid in str_results:
                row["liked"] = str_results[pid]

        # Update _display_data and visible rows
        for row_idx, row_data in enumerate(self._display_data):
            pid = str(row_data.get("post_id", ""))
            if pid in str_results:
                status = str_results[pid]
                row_data["liked"] = status
                item_id = str(row_idx)
                try:
                    values = list(self._tree.item(item_id, "values"))
                    values[liked_col_idx] = status
                    tags = self._compute_row_tags(row_idx, row_data, values)
                    self._tree.item(item_id, values=values, tags=tags)
                except tk.TclError:
                    pass

    # ------------------------------------------------------------------ #
    #  Cart count
    # ------------------------------------------------------------------ #

    def _update_cart_count(self):
        """Count and emit the number of [added] items."""
        count = 0
        for row_data in self._display_data:
            cart_val = str(row_data.get("download_cart", row_data.get("Download_Cart", "")))
            if cart_val == "[added]":
                count += 1

        if self._on_cart_count_changed is not None:
            try:
                self._on_cart_count_changed(count)
            except Exception as e:
                log.debug(f"cart_count_changed callback error: {e}")

        app_signals.download_cart_updated.emit(count)
