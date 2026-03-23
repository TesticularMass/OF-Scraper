import re
import tkinter as tk
from tkinter import ttk

import arrow

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c


class _CheckVar:
    """Thin wrapper around ttk.Checkbutton + BooleanVar providing a Qt-like API.

    Used by FilterSidebar so copy_filter_state_to() can call
    .isChecked() / .setChecked() uniformly.
    """

    def __init__(self, parent, text, checked=True, **kw):
        self._var = tk.BooleanVar(value=checked)
        self.widget = ttk.Checkbutton(parent, text=text, variable=self._var, **kw)

    def isChecked(self):
        return self._var.get()

    def setChecked(self, val):
        self._var.set(bool(val))

    # Layout helpers — delegate to the underlying widget
    def pack(self, **kw):
        self.widget.pack(**kw)

    def grid(self, **kw):
        self.widget.grid(**kw)


class _EntryVar:
    """Thin wrapper around ttk.Entry + StringVar providing a Qt-like API."""

    def __init__(self, parent, placeholder="", **kw):
        self._var = tk.StringVar()
        self.widget = ttk.Entry(parent, textvariable=self._var, **kw)
        self._placeholder = placeholder

    def text(self):
        return self._var.get()

    def setText(self, val):
        self._var.set(str(val))

    def clear(self):
        self._var.set("")

    def pack(self, **kw):
        self.widget.pack(**kw)

    def grid(self, **kw):
        self.widget.grid(**kw)


class _SpinVar:
    """Thin wrapper around ttk.Spinbox + DoubleVar providing .value()/.setValue()."""

    def __init__(self, parent, from_=0, to=99999, increment=1.0, **kw):
        self._var = tk.DoubleVar(value=0)
        self.widget = ttk.Spinbox(
            parent, textvariable=self._var,
            from_=from_, to=to, increment=increment, **kw
        )

    def value(self):
        try:
            return self._var.get()
        except (tk.TclError, ValueError):
            return 0.0

    def setValue(self, val):
        self._var.set(float(val))

    def pack(self, **kw):
        self.widget.pack(**kw)

    def grid(self, **kw):
        self.widget.grid(**kw)


class _DateVar:
    """Simple date entry wrapper — stores date as YYYY-MM-DD string."""

    def __init__(self, parent, **kw):
        self._var = tk.StringVar(value="")
        self.widget = ttk.Entry(parent, textvariable=self._var, width=12, **kw)

    def date_str(self):
        return self._var.get().strip()

    def setDate(self, val):
        """Accept a string (YYYY-MM-DD) or another _DateVar."""
        if isinstance(val, _DateVar):
            self._var.set(val.date_str())
        else:
            self._var.set(str(val))

    # Qt compat — area_selector_page calls .date() and .setDate()
    def date(self):
        return self

    def toString(self, fmt="yyyy-MM-dd"):
        return self.date_str()

    def pack(self, **kw):
        self.widget.pack(**kw)

    def grid(self, **kw):
        self.widget.grid(**kw)


class _TimeVar:
    """Simple time entry wrapper — stores time as HH:MM:SS string."""

    def __init__(self, parent, **kw):
        self._var = tk.StringVar(value="00:00:00")
        self.widget = ttk.Entry(parent, textvariable=self._var, width=10, **kw)

    def time_str(self):
        return self._var.get().strip() or "00:00:00"

    def setTime(self, val):
        if isinstance(val, _TimeVar):
            self._var.set(val.time_str())
        else:
            self._var.set(str(val))

    # Qt compat — area_selector_page calls .time()
    def time(self):
        return self

    def hour(self):
        parts = self.time_str().split(":")
        try:
            return int(parts[0])
        except (IndexError, ValueError):
            return 0

    def minute(self):
        parts = self.time_str().split(":")
        try:
            return int(parts[1])
        except (IndexError, ValueError):
            return 0

    def second(self):
        parts = self.time_str().split(":")
        try:
            return int(parts[2])
        except (IndexError, ValueError):
            return 0

    def pack(self, **kw):
        self.widget.pack(**kw)

    def grid(self, **kw):
        self.widget.grid(**kw)


class FilterState:
    """Manages the current filter values — replaces the TUI Status singleton."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.text_search = ""
        self.full_string_match = False
        self.mediatype = None  # None = all, or set of selected types
        self.responsetype = None  # None = all, or set of selected types
        self.downloaded = None  # None = all, or set of bools
        self.unlocked = None  # None = all, or set of bools
        self.mindate = None
        self.maxdate = None
        self.min_length = None
        self.max_length = None
        self.min_price = None
        self.max_price = None
        self.media_id = None
        self.post_id = None
        self.post_media_count = None
        self.other_posts_with_media = None
        self.username = None

    def validate(self, name, value):
        """Check if a row value passes the current filter for the given field."""
        name = name.lower()

        if name == "text":
            return self._text_validate(value)
        elif name == "mediatype":
            return self._set_validate(self.mediatype, value)
        elif name == "responsetype":
            return self._set_validate(self.responsetype, value)
        elif name == "downloaded":
            return self._bool_validate(self.downloaded, value)
        elif name == "unlocked":
            return self._bool_validate(self.unlocked, value)
        elif name == "post_date":
            return self._date_validate(value)
        elif name == "length":
            return self._length_validate(value)
        elif name == "price":
            return self._price_validate(value)
        elif name == "media_id":
            return self._exact_validate(self.media_id, value)
        elif name == "post_id":
            return self._exact_validate(self.post_id, value)
        elif name == "post_media_count":
            return self._exact_validate(self.post_media_count, value)
        elif name == "other_posts_with_media":
            return self._list_count_validate(
                self.other_posts_with_media, value
            )
        elif name == "username":
            return self._string_validate(self.username, value)
        return True

    def _text_validate(self, value):
        if not self.text_search:
            return True
        try:
            if self.full_string_match:
                return bool(
                    re.fullmatch(self.text_search, str(value), re.IGNORECASE)
                )
            else:
                return bool(
                    re.search(self.text_search, str(value), re.IGNORECASE)
                )
        except re.error:
            return self.text_search.lower() in str(value).lower()

    def _set_validate(self, filter_set, value):
        if filter_set is None:
            return True
        return str(value).lower() in {s.lower() for s in filter_set}

    def _bool_validate(self, filter_set, value):
        if filter_set is None:
            return True
        return value in filter_set

    def _date_validate(self, value):
        if self.mindate is None and self.maxdate is None:
            return True
        try:
            test_date = arrow.get(value).floor("day")
            if self.mindate and self.maxdate:
                return test_date.is_between(
                    arrow.get(self.mindate), arrow.get(self.maxdate), bounds="[]"
                )
            elif self.mindate:
                return test_date >= arrow.get(self.mindate)
            elif self.maxdate:
                return test_date <= arrow.get(self.maxdate)
        except Exception:
            return True
        return True

    def _length_validate(self, value):
        if self.min_length is None and self.max_length is None:
            return True
        try:
            if str(value) in ("N/A", "N\\A"):
                test_val = arrow.get("0:0:0", "h:m:s")
            else:
                test_val = arrow.get(str(value), "h:m:s")

            if self.min_length and self.max_length:
                return test_val.is_between(
                    self.min_length, self.max_length, bounds="[]"
                )
            elif self.min_length:
                return test_val >= self.min_length
            elif self.max_length:
                return test_val <= self.max_length
        except Exception:
            return True
        return True

    def _price_validate(self, value):
        if self.min_price is None and self.max_price is None:
            return True
        try:
            val = 0 if str(value).lower() == "free" else float(value)
            if self.min_price is not None and val < self.min_price:
                return False
            if self.max_price is not None and val > self.max_price:
                return False
        except (ValueError, TypeError):
            return True
        return True

    def _exact_validate(self, filter_val, value):
        if filter_val is None:
            return True
        return str(value).lower() == str(filter_val).lower()

    def _list_count_validate(self, filter_val, value):
        if filter_val is None:
            return True
        try:
            count = len(value) if isinstance(value, list) else int(value)
            return int(filter_val) == count
        except (ValueError, TypeError):
            return True

    def _string_validate(self, filter_val, value):
        if not filter_val:
            return True
        return str(filter_val).lower() in str(value).lower()


class FilterSidebar(ttk.Frame):
    """Filter sidebar with all filter fields — tkinter version."""

    def __init__(self, parent=None, embedded=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.state = FilterState()
        self._embedded = embedded
        self._setup_ui()

    def _setup_ui(self):
        if not self._embedded:
            # Scrollable version: canvas + scrollbar
            canvas = tk.Canvas(self, highlightthickness=0)
            scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
            self._scroll_frame = ttk.Frame(canvas)
            self._scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas_window = canvas.create_window((0, 0), window=self._scroll_frame, anchor=tk.NW)
            canvas.bind(
                "<Configure>",
                lambda e: canvas.itemconfig(canvas_window, width=e.width),
            )
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Mousewheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
            canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

            container = self._scroll_frame
        else:
            container = self

        # Title
        ttk.Label(container, text="Filters", font=("Segoe UI", 14, "bold")).pack(
            anchor=tk.W, padx=8, pady=(8, 4)
        )

        # -- Text search --
        text_group = ttk.LabelFrame(container, text="Text Search")
        text_group.pack(fill=tk.X, padx=8, pady=4)

        self.text_input = _EntryVar(text_group)
        self.text_input.pack(fill=tk.X, padx=8, pady=(4, 2))

        self.fullstring_check = _CheckVar(text_group, "Full string match", checked=False)
        self.fullstring_check.pack(anchor=tk.W, padx=8, pady=(0, 4))

        # -- Media type --
        media_group = ttk.LabelFrame(container, text="Media Type")
        media_group.pack(fill=tk.X, padx=8, pady=4)

        self.media_checks = {}
        for mt in ["audios", "images", "videos"]:
            cv = _CheckVar(media_group, mt.capitalize(), checked=True)
            cv.pack(anchor=tk.W, padx=8, pady=1)
            self.media_checks[mt] = cv

        # -- Response type --
        resp_group = ttk.LabelFrame(container, text="Response Type")
        resp_group.pack(fill=tk.X, padx=8, pady=4)

        self.resp_checks = {}
        for rt in ["pinned", "archived", "timeline", "stories", "highlights", "streams"]:
            cv = _CheckVar(resp_group, rt.capitalize(), checked=True)
            cv.pack(anchor=tk.W, padx=8, pady=1)
            self.resp_checks[rt] = cv

        # -- Downloaded / Unlocked --
        status_group = ttk.LabelFrame(container, text="Status")
        status_group.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(status_group, text="Downloaded:", style="Muted.TLabel").pack(
            anchor=tk.W, padx=8, pady=(4, 0)
        )
        dl_frame = ttk.Frame(status_group)
        dl_frame.pack(fill=tk.X, padx=8, pady=2)
        self.dl_true = _CheckVar(dl_frame, "True", checked=True)
        self.dl_true.pack(side=tk.LEFT, padx=(0, 8))
        self.dl_false = _CheckVar(dl_frame, "False", checked=True)
        self.dl_false.pack(side=tk.LEFT, padx=(0, 8))
        self.dl_no = _CheckVar(dl_frame, "No (Paid)", checked=True)
        self.dl_no.pack(side=tk.LEFT)

        ttk.Label(status_group, text="Unlocked:", style="Muted.TLabel").pack(
            anchor=tk.W, padx=8, pady=(4, 0)
        )
        ul_frame = ttk.Frame(status_group)
        ul_frame.pack(fill=tk.X, padx=8, pady=(2, 4))
        self.ul_true = _CheckVar(ul_frame, "True", checked=True)
        self.ul_true.pack(side=tk.LEFT, padx=(0, 8))
        self.ul_false = _CheckVar(ul_frame, "False", checked=True)
        self.ul_false.pack(side=tk.LEFT, padx=(0, 8))
        self.ul_not_paid = _CheckVar(ul_frame, "Locked", checked=True)
        self.ul_not_paid.pack(side=tk.LEFT)

        # -- Date range --
        date_group = ttk.LabelFrame(container, text="Post Date Range")
        date_group.pack(fill=tk.X, padx=8, pady=4)

        date_row = ttk.Frame(date_group)
        date_row.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(date_row, text="From:").pack(side=tk.LEFT, padx=(0, 4))
        self.min_date = _DateVar(date_row)
        self.min_date.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(date_row, text="To:").pack(side=tk.LEFT, padx=(0, 4))
        self.max_date = _DateVar(date_row)
        self.max_date.pack(side=tk.LEFT, padx=(0, 8))
        self.date_enabled = _CheckVar(date_row, "Enable", checked=False)
        self.date_enabled.pack(side=tk.LEFT)

        # -- Duration / Length --
        length_group = ttk.LabelFrame(container, text="Duration (Length)")
        length_group.pack(fill=tk.X, padx=8, pady=4)

        length_row = ttk.Frame(length_group)
        length_row.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(length_row, text="Min:").pack(side=tk.LEFT, padx=(0, 4))
        self.min_time = _TimeVar(length_row)
        self.min_time.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(length_row, text="Max:").pack(side=tk.LEFT, padx=(0, 4))
        self.max_time = _TimeVar(length_row)
        self.max_time.pack(side=tk.LEFT, padx=(0, 8))
        self.length_enabled = _CheckVar(length_row, "Enable", checked=False)
        self.length_enabled.pack(side=tk.LEFT)

        # -- Price range --
        price_group = ttk.LabelFrame(container, text="Price Range")
        price_group.pack(fill=tk.X, padx=8, pady=4)

        price_row = ttk.Frame(price_group)
        price_row.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(price_row, text="Min:").pack(side=tk.LEFT, padx=(0, 4))
        self.price_min = _SpinVar(price_row, from_=0, to=99999, increment=1.0)
        self.price_min.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(price_row, text="Max:").pack(side=tk.LEFT, padx=(0, 4))
        self.price_max = _SpinVar(price_row, from_=0, to=99999, increment=1.0)
        self.price_max.pack(side=tk.LEFT)

        # -- Numeric IDs --
        ids_group = ttk.LabelFrame(container, text="ID Filters")
        ids_group.pack(fill=tk.X, padx=8, pady=4)

        ids_inner = ttk.Frame(ids_group)
        ids_inner.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(ids_inner, text="Media ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.media_id_input = _EntryVar(ids_inner)
        self.media_id_input.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0), pady=2)

        ttk.Label(ids_inner, text="Post ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.post_id_input = _EntryVar(ids_inner)
        self.post_id_input.grid(row=1, column=1, sticky=tk.EW, padx=(8, 0), pady=2)

        ttk.Label(ids_inner, text="Post Media Count:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.post_media_count_input = _SpinVar(ids_inner, from_=0, to=99999)
        self.post_media_count_input.grid(row=2, column=1, sticky=tk.EW, padx=(8, 0), pady=2)

        ttk.Label(ids_inner, text="Other Posts w/ Media:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.other_posts_input = _SpinVar(ids_inner, from_=0, to=99999)
        self.other_posts_input.grid(row=3, column=1, sticky=tk.EW, padx=(8, 0), pady=2)

        ids_inner.columnconfigure(1, weight=1)

        # -- Username --
        user_group = ttk.LabelFrame(container, text="Username")
        user_group.pack(fill=tk.X, padx=8, pady=4)

        self.username_input = _EntryVar(user_group)
        self.username_input.pack(fill=tk.X, padx=8, pady=4)

    def collect_state(self):
        """Read all widget values into the FilterState object."""
        s = self.state

        # Text
        s.text_search = self.text_input.text().strip()
        s.full_string_match = self.fullstring_check.isChecked()

        # Media type
        selected_media = {
            mt for mt, cb in self.media_checks.items() if cb.isChecked()
        }
        s.mediatype = selected_media if len(selected_media) < 3 else None

        # Response type
        selected_resp = {
            rt for rt, cb in self.resp_checks.items() if cb.isChecked()
        }
        s.responsetype = selected_resp if len(selected_resp) < 6 else None

        # Downloaded / Unlocked (mixed bool + string values)
        dl_selected = set()
        if self.dl_true.isChecked():
            dl_selected.add(True)
            dl_selected.add("True")
        if self.dl_false.isChecked():
            dl_selected.add(False)
            dl_selected.add("False")
        if self.dl_no.isChecked():
            dl_selected.add("No")
        all_dl_checked = self.dl_true.isChecked() and self.dl_false.isChecked() and self.dl_no.isChecked()
        s.downloaded = dl_selected if not all_dl_checked else None

        ul_selected = set()
        if self.ul_true.isChecked():
            ul_selected.add(True)
            ul_selected.add("True")
        if self.ul_false.isChecked():
            ul_selected.add(False)
            ul_selected.add("False")
        if self.ul_not_paid.isChecked():
            ul_selected.add("Locked")
        all_ul_checked = self.ul_true.isChecked() and self.ul_false.isChecked() and self.ul_not_paid.isChecked()
        s.unlocked = ul_selected if not all_ul_checked else None

        # Date
        if self.date_enabled.isChecked():
            s.mindate = self.min_date.date_str() or None
            s.maxdate = self.max_date.date_str() or None
        else:
            s.mindate = None
            s.maxdate = None

        # Length
        if self.length_enabled.isChecked():
            mt = self.min_time
            if mt.hour() > 0 or mt.minute() > 0 or mt.second() > 0:
                s.min_length = arrow.get(
                    f"{mt.hour()}:{mt.minute()}:{mt.second()}", "h:m:s"
                )
            else:
                s.min_length = None
            xt = self.max_time
            if xt.hour() > 0 or xt.minute() > 0 or xt.second() > 0:
                s.max_length = arrow.get(
                    f"{xt.hour()}:{xt.minute()}:{xt.second()}", "h:m:s"
                )
            else:
                s.max_length = None
        else:
            s.min_length = None
            s.max_length = None

        # Price
        s.min_price = self.price_min.value() if self.price_min.value() > 0 else None
        s.max_price = self.price_max.value() if self.price_max.value() > 0 else None

        # IDs
        s.media_id = self.media_id_input.text().strip() or None
        s.post_id = self.post_id_input.text().strip() or None
        s.post_media_count = (
            int(self.post_media_count_input.value())
            if self.post_media_count_input.value() > 0
            else None
        )
        s.other_posts_with_media = (
            int(self.other_posts_input.value())
            if self.other_posts_input.value() > 0
            else None
        )

        # Username
        s.username = self.username_input.text().strip() or None

        return s

    def reset_all(self):
        """Reset all filter widgets to defaults."""
        self.text_input.clear()
        self.fullstring_check.setChecked(False)
        for cb in self.media_checks.values():
            cb.setChecked(True)
        for cb in self.resp_checks.values():
            cb.setChecked(True)
        self.dl_true.setChecked(True)
        self.dl_false.setChecked(True)
        self.dl_no.setChecked(True)
        self.ul_true.setChecked(True)
        self.ul_false.setChecked(True)
        self.ul_not_paid.setChecked(True)
        self.date_enabled.setChecked(False)
        self.min_date.setDate("")
        self.max_date.setDate("")
        self.length_enabled.setChecked(False)
        self.min_time.setTime("00:00:00")
        self.max_time.setTime("00:00:00")
        self.price_min.setValue(0)
        self.price_max.setValue(0)
        self.media_id_input.clear()
        self.post_id_input.clear()
        self.post_media_count_input.setValue(0)
        self.other_posts_input.setValue(0)
        self.username_input.clear()
        self.state.reset()

    def update_field(self, field_name, value):
        """Set a specific filter field value (e.g., from right-click on table cell)."""
        field_name = field_name.lower()
        if field_name == "text":
            self.text_input.setText(str(value))
        elif field_name == "username":
            self.username_input.setText(str(value))
        elif field_name == "media_id":
            self.media_id_input.setText(str(value))
        elif field_name == "post_id":
            self.post_id_input.setText(str(value))
