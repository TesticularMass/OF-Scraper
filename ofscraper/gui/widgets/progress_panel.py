import tkinter as tk
from tkinter import ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c


class ProgressSummaryBar(ttk.Frame):
    """Compact overall progress bar for embedding in a status/footer area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self._peak_bytes = 0

        self.overall_label = ttk.Label(
            self, text="Downloads: 0 / 0", style="Muted.TLabel"
        )
        self.overall_label.pack(side=tk.LEFT, padx=(0, 8))

        self._progress_var = tk.DoubleVar(value=0)
        self.overall_progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            mode="determinate",
            maximum=100,
            variable=self._progress_var,
            length=200,
        )
        self.overall_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.bytes_label = ttk.Label(
            self, text="Total: 0 B", style="Muted.TLabel"
        )
        self.bytes_label.pack(side=tk.LEFT)

        self.configure(height=22)

    def _connect_signals(self):
        app_signals.overall_progress_updated.connect(self._update_overall)
        app_signals.total_bytes_updated.connect(self._update_bytes)

    def _update_overall(self, completed, total):
        self.overall_label.configure(text=f"Downloads: {completed} / {total}")
        if total > 0:
            self._progress_var.set(int((completed / total) * 100))
        else:
            self._progress_var.set(0)

    def _update_bytes(self, total_bytes):
        self._peak_bytes = max(self._peak_bytes, total_bytes)
        self.bytes_label.configure(text=f"Total: {_format_bytes(self._peak_bytes)}")

    def clear_all(self):
        self._peak_bytes = 0
        self._progress_var.set(0)
        self.overall_label.configure(text="Downloads: 0 / 0")
        self.bytes_label.configure(text="Total: 0 B")


class ProgressPanel(ttk.Frame):
    """Panel displaying download progress bars and statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks = {}  # task_id -> (DoubleVar, ttk.Frame)
        self._task_maximums = {}  # task_id -> int (max value for the bar)
        self._task_currents = {}  # task_id -> int (current value)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self._peak_bytes = 0

        # Overall stats row
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        self.overall_label = ttk.Label(
            stats_frame, text="Downloads: 0 / 0", style="Subheading.TLabel"
        )
        self.overall_label.pack(side=tk.LEFT)

        self.bytes_label = ttk.Label(
            stats_frame, text="Total: 0 B", style="Muted.TLabel"
        )
        self.bytes_label.pack(side=tk.LEFT, padx=(12, 0))

        # Overall progress bar
        self._overall_var = tk.DoubleVar(value=0)
        self.overall_progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            mode="determinate",
            maximum=100,
            variable=self._overall_var,
        )
        self.overall_progress.pack(fill=tk.X, padx=8, pady=(0, 4))

        # Scrollable area for per-file progress bars
        scroll_frame = ttk.Frame(self)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._canvas = tk.Canvas(scroll_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            scroll_frame, orient=tk.VERTICAL, command=self._canvas.yview
        )
        self.tasks_container = ttk.Frame(self._canvas)

        self.tasks_container.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self.tasks_container, anchor=tk.NW
        )

        # Make the inner frame stretch to canvas width
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._canvas_window, width=e.width),
        )

        self._canvas.configure(yscrollcommand=scrollbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel scrolling
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, event):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _connect_signals(self):
        app_signals.progress_task_added.connect(self._add_task)
        app_signals.progress_task_updated.connect(self._update_task)
        app_signals.progress_task_removed.connect(self._remove_task)
        app_signals.overall_progress_updated.connect(self._update_overall)
        app_signals.total_bytes_updated.connect(self._update_bytes)

    def _add_task(self, task_id, total):
        if task_id in self._tasks:
            return

        row = ttk.Frame(self.tasks_container)
        row.pack(fill=tk.X, pady=2)

        label = ttk.Label(row, text=task_id, style="Muted.TLabel")
        label.pack(fill=tk.X)

        max_val = max(total, 1)
        progress_var = tk.DoubleVar(value=0)
        bar = ttk.Progressbar(
            row,
            orient=tk.HORIZONTAL,
            mode="determinate",
            maximum=max_val,
            variable=progress_var,
        )
        bar.pack(fill=tk.X)

        self._tasks[task_id] = (progress_var, row)
        self._task_maximums[task_id] = max_val
        self._task_currents[task_id] = 0

    def _update_task(self, task_id, advance):
        if task_id not in self._tasks:
            return
        progress_var, _ = self._tasks[task_id]
        max_val = self._task_maximums[task_id]
        current = self._task_currents[task_id]
        new_val = min(current + advance, max_val)
        self._task_currents[task_id] = new_val
        progress_var.set(new_val)

    def _remove_task(self, task_id):
        if task_id not in self._tasks:
            return
        _, row = self._tasks.pop(task_id)
        self._task_maximums.pop(task_id, None)
        self._task_currents.pop(task_id, None)
        row.destroy()

    def _update_overall(self, completed, total):
        self.overall_label.configure(text=f"Downloads: {completed} / {total}")
        if total > 0:
            self._overall_var.set(int((completed / total) * 100))
        else:
            self._overall_var.set(0)

    def _update_bytes(self, total_bytes):
        self._peak_bytes = max(self._peak_bytes, total_bytes)
        self.bytes_label.configure(text=f"Total: {_format_bytes(self._peak_bytes)}")

    def clear_all(self):
        self._peak_bytes = 0
        for task_id in list(self._tasks.keys()):
            self._remove_task(task_id)
        self._overall_var.set(0)
        self.overall_label.configure(text="Downloads: 0 / 0")
        self.bytes_label.configure(text="Total: 0 B")


def _format_bytes(num_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
