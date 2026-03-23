import logging
import tkinter as tk
from tkinter import ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c

log = logging.getLogger("shared")

ACTION_CHOICES = [
    ("Download content from a user", {"download"}),
    ("Like a selection of a user's posts", {"like"}),
    ("Unlike a selection of a user's posts", {"unlike"}),
    ("Download + Like", {"like", "download"}),
    ("Download + Unlike", {"unlike", "download"}),
    ("Subscribe to free accounts", {"subscribe"}),
]

_ACTION_TIPS = {
    "Download content from a user": "Scrape media from selected content areas and build the download table.\nYou can then select items to download from the table.",
    "Like a selection of a user's posts": "Automatically like posts in the selected content areas for chosen models.",
    "Unlike a selection of a user's posts": "Automatically unlike previously liked posts in the selected content areas.",
    "Download + Like": "Scrape and download content, then also like the posts.",
    "Download + Unlike": "Scrape and download content, then also unlike previously liked posts.",
    "Subscribe to free accounts": "Subscribe to expired accounts that are currently free or have a claimable $0 promotion.\nFilters selected models to only free/on-sale-for-$0, expired ones and sends subscribe requests.",
}

CHECK_CHOICES = [
    ("Check posts: build table of timeline/pinned/archived media", {"post_check"}),
    ("Check messages: build table of message & paid media", {"msg_check"}),
    ("Check paid content: build table of all paid/purchased media", {"paid_check"}),
    ("Check stories: build table of story & highlight media", {"story_check"}),
]

_CHECK_TIPS = {
    "Check posts: build table of timeline/pinned/archived media":
        "Fetches timeline, pinned, archived, label, and stream posts for the selected models\n"
        "and builds an interactive table showing downloaded/unlocked status.\n"
        "Select items in the table then click 'Send Downloads' to download them.",
    "Check messages: build table of message & paid media":
        "Fetches direct messages and paid content for the selected models\n"
        "and builds a browsable table. Select items to download.",
    "Check paid content: build table of all paid/purchased media":
        "Fetches all purchased/paid content for the selected models\n"
        "and builds a browsable table. Select items to download.",
    "Check stories: build table of story & highlight media":
        "Fetches stories and highlights for the selected models\n"
        "and builds a browsable table. Select items to download.",
}

ALL_CHOICES = ACTION_CHOICES + CHECK_CHOICES


class ActionPage(ttk.Frame):
    """Action selection page — replaces the InquirerPy action prompt."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._selected_actions = ACTION_CHOICES[0][1]
        self._radio_var = tk.IntVar(value=0)
        self._setup_ui()

    def _setup_ui(self):
        # Outer padding frame
        pad = ttk.Frame(self)
        pad.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Header
        header = ttk.Label(pad, text="Select Action", style="Heading.TLabel")
        header.pack(anchor=tk.W)

        subtitle = ttk.Label(
            pad,
            text="Choose what you want to do with the selected models.",
            style="Subheading.TLabel",
        )
        subtitle.pack(anchor=tk.W, pady=(0, 16))

        # Action radio buttons
        for i, (label, actions) in enumerate(ACTION_CHOICES):
            rb = ttk.Radiobutton(
                pad,
                text=label,
                variable=self._radio_var,
                value=i,
                command=self._on_action_changed,
            )
            rb.pack(anchor=tk.W, pady=4)

        # Separator between action modes and check modes
        sep = ttk.Separator(pad, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=(12, 8))

        check_label = ttk.Label(
            pad,
            text="Check Modes  (browse & selectively download)",
            style="Subheading.TLabel",
        )
        check_label.pack(anchor=tk.W, pady=(0, 4))

        for i, (label, actions) in enumerate(CHECK_CHOICES):
            rb = ttk.Radiobutton(
                pad,
                text=label,
                variable=self._radio_var,
                value=len(ACTION_CHOICES) + i,
                command=self._on_action_changed,
            )
            rb.pack(anchor=tk.W, pady=4)

        # Spacer
        spacer = ttk.Frame(pad)
        spacer.pack(fill=tk.BOTH, expand=True)

        # Bottom buttons
        btn_frame = ttk.Frame(pad)
        btn_frame.pack(fill=tk.X, pady=(16, 0))

        self.next_btn = ttk.Button(
            btn_frame,
            text="Next  >>",
            style="Primary.TButton",
            command=self._on_next,
            width=20,
        )
        self.next_btn.pack(side=tk.RIGHT)

    def reset_to_defaults(self):
        """Reset action selection to the first option (default)."""
        self._radio_var.set(0)
        self._selected_actions = ACTION_CHOICES[0][1]

    def _on_action_changed(self):
        btn_id = self._radio_var.get()
        if 0 <= btn_id < len(ALL_CHOICES):
            self._selected_actions = ALL_CHOICES[btn_id][1]

    def _on_next(self):
        if self._selected_actions:
            log.info(f"Actions selected: {self._selected_actions}")
            app_signals.action_selected.emit(self._selected_actions)
        else:
            app_signals.error_occurred.emit(
                "No Action", "Please select an action to continue."
            )
