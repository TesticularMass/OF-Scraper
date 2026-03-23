import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.widgets.styled_button import StyledButton

log = logging.getLogger("shared")


class BinaryDialog(ttk.Frame):
    """FFmpeg path configuration -- replaces the binary prompt."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        pad_x = 24
        pad_y = 8

        header = ttk.Label(self, text="FFmpeg Configuration",
                           font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", padx=pad_x, pady=(pad_y * 3, 4))

        info = ttk.Label(
            self,
            text="FFmpeg is required for merging audio/video streams and DRM content. "
                 "Set the path to your ffmpeg binary.",
            style="Muted.TLabel",
            wraplength=600,
        )
        info.pack(anchor="w", padx=pad_x, pady=(0, pad_y * 2))

        # Path input row
        path_frame = ttk.Frame(self)
        path_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        self.path_input = ttk.Entry(path_frame)
        self.path_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        browse_btn = StyledButton(path_frame, text="Browse",
                                  command=self._browse)
        browse_btn.pack(side=tk.LEFT)

        # Save button
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        save_btn = StyledButton(btn_frame, text="Save", primary=True,
                                command=self._save)
        save_btn.pack(side=tk.RIGHT)

        self._load()

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select FFmpeg Binary",
            filetypes=[("All Files", "*.*")],
        )
        if path:
            self.path_input.delete(0, tk.END)
            self.path_input.insert(0, path)

    def _load(self):
        try:
            from ofscraper.utils.config.config import read_config
            config = read_config(update=False) or {}
            binary = config.get("binary_options", {})
            ffmpeg_path = binary.get("ffmpeg", "")
            if ffmpeg_path:
                self.path_input.delete(0, tk.END)
                self.path_input.insert(0, ffmpeg_path)
        except Exception:
            pass

    def _save(self):
        try:
            from ofscraper.utils.config.config import read_config
            from ofscraper.utils.config.file import write_config

            config = read_config(update=False) or {}
            if "binary_options" not in config:
                config["binary_options"] = {}
            config["binary_options"]["ffmpeg"] = self.path_input.get().strip()
            write_config(config)
            app_signals.status_message.emit("FFmpeg path saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
