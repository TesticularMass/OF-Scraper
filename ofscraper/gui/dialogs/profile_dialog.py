import logging
import pathlib
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c
from ofscraper.gui.widgets.styled_button import StyledButton

log = logging.getLogger("shared")


class ProfilePage(ttk.Frame):
    """Profile manager page -- replaces the InquirerPy profile prompts."""

    def __init__(self, parent, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._setup_ui()
        self._load_profiles()

    def _setup_ui(self):
        pad_x = 40
        pad_y = 8

        # Header
        header = ttk.Label(self, text="Profile Manager", style="Heading.TLabel")
        header.pack(anchor="w", padx=pad_x, pady=(pad_y * 3, 4))

        subtitle = ttk.Label(
            self,
            text="Manage your profiles. Each profile has its own auth.json and data directories.",
            style="Subheading.TLabel",
            wraplength=700,
        )
        subtitle.pack(anchor="w", padx=pad_x, pady=(0, pad_y))

        # Current profile indicator
        self.current_label = ttk.Label(
            self, text="Current profile: loading...",
            font=("Segoe UI", 13), foreground=c("blue"),
        )
        self.current_label.pack(anchor="w", padx=pad_x, pady=(0, pad_y))

        app_signals.theme_changed.connect(
            lambda _: self.current_label.configure(foreground=c("blue"))
        )

        # Content area: list + buttons side by side
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=pad_x, pady=pad_y)

        # Profile list
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.profile_list = tk.Listbox(
            list_frame, selectmode=tk.SINGLE, font=("Segoe UI", 12),
            relief=tk.SUNKEN, borderwidth=1,
        )
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                       command=self.profile_list.yview)
        self.profile_list.configure(yscrollcommand=list_scrollbar.set)

        self.profile_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(16, 0))

        self.set_default_btn = StyledButton(btn_frame, text="Set as Default",
                                            primary=True, command=self._set_default)
        self.set_default_btn.pack(fill=tk.X, pady=(0, 8))

        self.create_btn = StyledButton(btn_frame, text="Create Profile",
                                       command=self._create_profile)
        self.create_btn.pack(fill=tk.X, pady=(0, 8))

        self.rename_btn = StyledButton(btn_frame, text="Rename",
                                       command=self._rename_profile)
        self.rename_btn.pack(fill=tk.X, pady=(0, 8))

        self.delete_btn = StyledButton(btn_frame, text="Delete",
                                       danger=True, command=self._delete_profile)
        self.delete_btn.pack(fill=tk.X, pady=(0, 8))

        # Spacer
        spacer = ttk.Frame(btn_frame)
        spacer.pack(fill=tk.Y, expand=True)

        self.refresh_btn = StyledButton(btn_frame, text="Refresh",
                                        command=self._load_profiles)
        self.refresh_btn.pack(fill=tk.X)

    def _load_profiles(self):
        """Load profile list from disk."""
        self.profile_list.delete(0, tk.END)
        try:
            from ofscraper.utils.profiles.data import get_profile_names
            from ofscraper.utils.profiles.data import get_active_profile

            profiles = get_profile_names()
            active = get_active_profile()

            self.current_label.configure(text=f"Current profile: {active}")

            for name in profiles:
                if name == active:
                    display = f"{name} (active)"
                    idx = self.profile_list.size()
                    self.profile_list.insert(tk.END, display)
                    self.profile_list.itemconfigure(idx, foreground=c("blue"))
                else:
                    self.profile_list.insert(tk.END, name)

            app_signals.status_message.emit(f"Found {len(profiles)} profiles")
        except Exception as e:
            log.error(f"Failed to load profiles: {e}")
            app_signals.status_message.emit(f"Failed to load profiles: {e}")

    def _get_selected_profile(self):
        """Get the selected profile name (strip active marker)."""
        selection = self.profile_list.curselection()
        if not selection:
            return None
        text = self.profile_list.get(selection[0])
        name = text.replace(" (active)", "")
        return name

    def _set_default(self):
        """Set selected profile as the default."""
        name = self._get_selected_profile()
        if not name:
            messagebox.showwarning("No Selection", "Select a profile first.")
            return

        try:
            from ofscraper.utils.config.config import update_config
            clean_name = name.replace("_profile", "")
            update_config("main_profile", clean_name)
            app_signals.status_message.emit(f"Default profile set to: {name}")
            self._load_profiles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set default: {e}")

    def _create_profile(self):
        """Create a new profile."""
        text = simpledialog.askstring(
            "Create Profile", "Enter new profile name:",
            parent=self,
        )
        if not text or not text.strip():
            return

        name = text.strip()
        if not name.endswith("_profile"):
            name = f"{name}_profile"

        try:
            from ofscraper.utils.paths.common import get_config_home
            profile_path = get_config_home() / name
            if profile_path.exists():
                messagebox.showwarning(
                    "Exists", f"Profile '{name}' already exists."
                )
                return

            profile_path.mkdir(parents=True, exist_ok=True)
            app_signals.status_message.emit(f"Created profile: {name}")
            self._load_profiles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create profile: {e}")

    def _rename_profile(self):
        """Rename the selected profile."""
        old_name = self._get_selected_profile()
        if not old_name:
            messagebox.showwarning("No Selection", "Select a profile first.")
            return

        display = old_name.replace("_profile", "")
        text = simpledialog.askstring(
            "Rename Profile", "Enter new name:",
            parent=self, initialvalue=display,
        )
        if not text or not text.strip():
            return

        new_name = text.strip()
        if not new_name.endswith("_profile"):
            new_name = f"{new_name}_profile"

        try:
            from ofscraper.utils.paths.common import get_config_home
            old_path = get_config_home() / old_name
            new_path = get_config_home() / new_name

            if new_path.exists():
                messagebox.showwarning(
                    "Exists", f"Profile '{new_name}' already exists."
                )
                return

            if old_path.exists():
                old_path.rename(new_path)
                app_signals.status_message.emit(
                    f"Renamed '{old_name}' to '{new_name}'"
                )
            self._load_profiles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename: {e}")

    def _delete_profile(self):
        """Delete the selected profile."""
        name = self._get_selected_profile()
        if not name:
            messagebox.showwarning("No Selection", "Select a profile first.")
            return

        reply = messagebox.askyesno(
            "Delete Profile",
            f"Are you sure you want to delete profile '{name}'?\n"
            "This will remove all data associated with this profile.",
        )
        if not reply:
            return

        try:
            from ofscraper.utils.paths.common import get_config_home
            profile_path = get_config_home() / name
            if profile_path.exists():
                shutil.rmtree(profile_path)
                app_signals.status_message.emit(f"Deleted profile: {name}")
            self._load_profiles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")
