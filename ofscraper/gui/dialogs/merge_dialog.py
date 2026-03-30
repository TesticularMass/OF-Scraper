import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c
from ofscraper.gui.utils.thread_worker import AsyncWorker
from ofscraper.gui.widgets.styled_button import StyledButton

log = logging.getLogger("shared")


class MergePage(ttk.Frame):
    """Database merge page -- replaces the InquirerPy merge prompts."""

    def __init__(self, parent, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._setup_ui()

    def _setup_ui(self):
        pad_x = 40
        pad_y = 8

        # Header
        header = ttk.Label(self, text="Merge Databases", style="Heading.TLabel")
        header.pack(anchor="w", padx=pad_x, pady=(pad_y * 3, 4))

        subtitle = ttk.Label(
            self,
            text="Recursively search a folder for user_data.db files and merge them "
                 "into a single destination database.",
            style="Subheading.TLabel",
            wraplength=700,
        )
        subtitle.pack(anchor="w", padx=pad_x, pady=(0, pad_y * 2))

        # Source folder
        src_frame = ttk.Frame(self)
        src_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        ttk.Label(src_frame, text="Source Folder:").pack(side=tk.LEFT)

        self.source_input = ttk.Entry(src_frame)
        self.source_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))

        src_browse = StyledButton(src_frame, text="Browse",
                                  command=self._browse_source)
        src_browse.pack(side=tk.LEFT)

        # Destination
        dst_frame = ttk.Frame(self)
        dst_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        ttk.Label(dst_frame, text="Destination:").pack(side=tk.LEFT)

        self.dest_input = ttk.Entry(dst_frame)
        self.dest_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))

        dst_browse = StyledButton(dst_frame, text="Browse",
                                  command=self._browse_dest)
        dst_browse.pack(side=tk.LEFT)

        # Warning
        self._warning_label = ttk.Label(
            self,
            text="WARNING: Make sure you have backed up your databases before merging!",
            font=("Segoe UI", 11, "bold"),
            foreground=c("warning"),
        )
        self._warning_label.pack(anchor="w", padx=pad_x, pady=pad_y)

        app_signals.theme_changed.connect(self._apply_theme)

        # Merge button
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        self.merge_btn = StyledButton(btn_frame, text="Start Merge",
                                      primary=True, command=self._on_merge)
        self.merge_btn.pack(side=tk.RIGHT)

        # Output log
        self.output_text = tk.Text(self, wrap=tk.WORD, height=14,
                                   font=("Consolas", 9), state=tk.DISABLED,
                                   relief=tk.SUNKEN, borderwidth=1)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=pad_x, pady=(pad_y, pad_y * 3))

    def _apply_theme(self, _is_dark=True):
        self._warning_label.configure(foreground=c("warning"))

    def _text_clear(self):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _text_append(self, text):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.source_input.delete(0, tk.END)
            self.source_input.insert(0, folder)

    def _browse_dest(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.dest_input.delete(0, tk.END)
            self.dest_input.insert(0, folder)

    def _on_merge(self):
        source = self.source_input.get().strip()
        dest = self.dest_input.get().strip()

        if not source:
            messagebox.showwarning("Missing", "Please select a source folder.")
            return
        if not dest:
            messagebox.showwarning("Missing", "Please select a destination folder.")
            return

        reply = messagebox.askyesno(
            "Confirm Merge",
            f"Merge databases from:\n{source}\n\nInto:\n{dest}\n\nContinue?",
        )
        if not reply:
            return

        self._text_clear()
        self._text_append(f"Starting merge from {source} to {dest}...")
        self.merge_btn.configure(state=tk.DISABLED)
        app_signals.status_message.emit("Merge in progress...")

        # Run merge in background thread (store ref to prevent GC)
        self._worker = AsyncWorker(self._run_merge, source, dest)
        self._worker.signals.finished.connect(self._on_merge_finished)
        self._worker.signals.error.connect(self._on_merge_error)
        self._worker.start()

    async def _run_merge(self, source, dest):
        from ofscraper.db.merge import MergeDatabase
        merger = MergeDatabase()
        return await merger(source, dest)

    def _on_merge_finished(self, result):
        self.merge_btn.configure(state=tk.NORMAL)
        if result:
            failures, successes, _ = result
            self._text_append(
                f"\nMerge complete!\n"
                f"Successes: {len(successes) if successes else 0}\n"
                f"Failures: {len(failures) if failures else 0}"
            )
            if failures:
                for f in failures:
                    self._text_append(f"  FAILED: {f}")
        else:
            self._text_append("Merge completed (no details returned).")
        app_signals.status_message.emit("Merge complete")

    def _on_merge_error(self, error_msg):
        self.merge_btn.configure(state=tk.NORMAL)
        self._text_append(f"\nERROR: {error_msg}")
        app_signals.status_message.emit("Merge failed")
        messagebox.showerror("Merge Error", error_msg)
