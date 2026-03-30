import logging
import tkinter as tk
from tkinter import messagebox, ttk

log = logging.getLogger("shared")


class MissingDepsDialog(tk.Toplevel):
    """Single popup that warns about missing ffmpeg / manual CDM key paths."""

    def __init__(
        self,
        *,
        missing_ffmpeg,
        missing_manual_cdm,
        on_open_ffmpeg=None,
        on_open_cdm=None,
        on_open_drm=None,
        parent=None,
    ):
        super().__init__(parent)
        self._missing_ffmpeg = bool(missing_ffmpeg)
        self._missing_manual_cdm = bool(missing_manual_cdm)
        self._on_open_ffmpeg = on_open_ffmpeg
        self._on_open_cdm = on_open_cdm
        self._on_open_drm = on_open_drm

        self.title("Missing configuration paths")
        self.minsize(720, 400)
        self.resizable(True, True)

        # Make modal
        if parent:
            self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._setup_ui()

        # Center on parent
        self.update_idletasks()
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
            y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{x}+{y}")

        self.wait_window()

    def _setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(16, 14))

        title = ttk.Label(
            main_frame,
            text="Missing required file paths in config.json",
            font=("Segoe UI", 13, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main_frame,
            text="Some features require external binaries/keys. Add the missing paths below.",
            style="Muted.TLabel",
            wraplength=680,
        )
        subtitle.pack(anchor="w", pady=(4, 10))

        # Info text area
        viewer = tk.Text(main_frame, wrap=tk.WORD, height=12,
                         relief=tk.SUNKEN, borderwidth=1,
                         font=("Segoe UI", 10), state=tk.NORMAL)
        viewer.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._insert_info_text(viewer)

        viewer.configure(state=tk.DISABLED)

        # Action buttons (conditional)
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        # Spacer to push buttons right
        spacer = ttk.Frame(actions_frame)
        spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if self._missing_ffmpeg:
            self.ffmpeg_btn = ttk.Button(
                actions_frame,
                text="Open Config -> Download (FFmpeg)",
                command=self._open_ffmpeg,
            )
            self.ffmpeg_btn.pack(side=tk.LEFT, padx=(0, 8))

        if self._missing_manual_cdm:
            self.drm_btn = ttk.Button(
                actions_frame,
                text="Generate DRM Keys",
                command=self._open_drm,
            )
            self.drm_btn.pack(side=tk.LEFT, padx=(0, 8))

            self.cdm_btn = ttk.Button(
                actions_frame,
                text="Open Config -> CDM (Manual keys)",
                command=self._open_cdm,
            )
            self.cdm_btn.pack(side=tk.LEFT)

        # Close button
        close_frame = ttk.Frame(main_frame)
        close_frame.pack(fill=tk.X)

        close_btn = ttk.Button(close_frame, text="Close", command=self.destroy)
        close_btn.pack(side=tk.RIGHT)

    def _insert_info_text(self, text_widget):
        """Insert the informational text into the Text widget with basic formatting."""
        # Configure tags for formatting
        text_widget.tag_configure("h3", font=("Segoe UI", 12, "bold"),
                                  spacing1=8, spacing3=4)
        text_widget.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        text_widget.tag_configure("normal", font=("Segoe UI", 10))
        text_widget.tag_configure("code", font=("Consolas", 10))
        text_widget.tag_configure("hr", font=("Segoe UI", 4),
                                  spacing1=6, spacing3=6)

        sections = []

        if self._missing_ffmpeg:
            sections.append("ffmpeg")

        if self._missing_manual_cdm:
            sections.append("cdm")

        if not sections:
            text_widget.insert(tk.END, "No missing settings detected.", "normal")
            return

        first = True
        for section in sections:
            if not first:
                text_widget.insert(tk.END, "\n" + "-" * 60 + "\n", "hr")
            first = False

            if section == "ffmpeg":
                text_widget.insert(tk.END, "FFmpeg\n", "h3")
                text_widget.insert(tk.END,
                    "Missing file path for FFmpeg in your config. "
                    "This is needed to merge DRM protected audio and video files.\n\n",
                    "normal")
                text_widget.insert(tk.END,
                    "Use version 7.1.1 or lower from:\n"
                    "https://www.gyan.dev/ffmpeg/builds\n",
                    "normal")

            elif section == "cdm":
                text_widget.insert(tk.END, "Manual CDM keys\n", "h3")
                text_widget.insert(tk.END,
                    "Manual DRM key paths are not set in your config. "
                    "These are required to scrape DRM-protected content.\n\n",
                    "normal")
                text_widget.insert(tk.END,
                    "Already have keys? ", "bold")
                text_widget.insert(tk.END,
                    "Click 'Open Config -> CDM (Manual keys)' to enter the paths "
                    "to your client_id.bin and private_key.pem files.\n\n",
                    "normal")
                text_widget.insert(tk.END,
                    "Don't have keys yet? ", "bold")
                text_widget.insert(tk.END,
                    "Click 'Generate DRM Keys' to use the built-in extraction "
                    "tool to create them automatically.\n",
                    "normal")

    def _confirm_jump(self, title, msg):
        try:
            return messagebox.askyesno(title, msg, parent=self)
        except Exception:
            return True

    def _open_drm(self):
        if not callable(self._on_open_drm):
            return
        self._on_open_drm()
        self.destroy()

    def _open_ffmpeg(self):
        if not callable(self._on_open_ffmpeg):
            return
        if self._confirm_jump(
            "Open Configuration?",
            "Open Configuration to the Download tab to enter the FFmpeg file path?",
        ):
            self._on_open_ffmpeg()
            self.destroy()

    def _open_cdm(self):
        if not callable(self._on_open_cdm):
            return
        if self._confirm_jump(
            "Open Configuration?",
            "Open Configuration to the CDM tab to enter the manual DRM key paths?",
        ):
            self._on_open_cdm()
            self.destroy()
