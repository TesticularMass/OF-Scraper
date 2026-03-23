"""Styled button widgets for the tkinter GUI.

Provides StyledButton and NavButton as thin wrappers around ttk.Button
with appropriate style classes applied.
"""

from tkinter import ttk


class StyledButton(ttk.Button):
    """Standard styled button matching the app theme."""

    def __init__(self, parent=None, text="", primary=False, danger=False, **kwargs):
        if primary:
            style = "Primary.TButton"
        elif danger:
            style = "Danger.TButton"
        else:
            style = "TButton"
        super().__init__(parent, text=text, style=style, **kwargs)


class NavButton(ttk.Button):
    """Navigation sidebar button with selectable state."""

    def __init__(self, parent=None, text="", **kwargs):
        super().__init__(parent, text=text, style="Nav.TButton", **kwargs)
        self._is_active = False

    def set_active(self, active: bool):
        """Toggle the active/selected visual state."""
        self._is_active = active
        self.configure(style="NavActive.TButton" if active else "Nav.TButton")
