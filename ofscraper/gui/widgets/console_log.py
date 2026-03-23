"""Console log widget for the tkinter GUI.

Displays application logs with color-coded severity levels using a tk.Text widget.
"""

import tkinter as tk
from tkinter import ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c


class ConsoleLogWidget(ttk.Frame):
    """Log viewer widget that displays application logs with color-coded levels."""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Use a tk.Text widget for rich formatting
        self.text_widget = tk.Text(
            self,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 11),
            bg=c("mantle"),
            fg=c("green"),
            insertbackground=c("text"),
            selectbackground=c("blue"),
            selectforeground=c("base"),
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=c("surface0"),
            highlightcolor=c("blue"),
        )
        self.text_widget.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL,
                                  command=self.text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        # Configure color tags
        self._configure_tags()

    def _configure_tags(self):
        """Set up text tags for each log level."""
        self.text_widget.tag_configure("DEBUG", foreground=c("subtext"))
        self.text_widget.tag_configure("INFO", foreground=c("green"))
        self.text_widget.tag_configure("WARNING", foreground=c("yellow"))
        self.text_widget.tag_configure("ERROR", foreground=c("red"))
        self.text_widget.tag_configure("CRITICAL", foreground=c("red"))
        self.text_widget.tag_configure("DEFAULT", foreground=c("text"))

    def _connect_signals(self):
        app_signals.log_message.connect(self._append_log)

    def _append_log(self, level, message):
        """Append a log message with the appropriate color tag."""
        tag = level.upper() if level.upper() in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL") else "DEFAULT"
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + "\n", tag)

        # Limit to ~10000 lines
        line_count = int(self.text_widget.index("end-1c").split(".")[0])
        if line_count > 10000:
            self.text_widget.delete("1.0", f"{line_count - 10000}.0")

        self.text_widget.see(tk.END)
        self.text_widget.configure(state=tk.DISABLED)

    def clear_log(self):
        """Clear all log content."""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.configure(state=tk.DISABLED)

    def update_theme(self):
        """Re-apply theme colors when theme changes."""
        self.text_widget.configure(
            bg=c("mantle"),
            fg=c("green"),
            highlightbackground=c("surface0"),
            highlightcolor=c("blue"),
            selectbackground=c("blue"),
            selectforeground=c("base"),
        )
        self._configure_tags()
