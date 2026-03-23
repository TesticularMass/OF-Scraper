"""Theme management for the tkinter GUI.

Provides dark (Catppuccin Mocha) and light (Catppuccin Latte) themes
using ttk styling.  The module-level ``c(name)`` helper returns the
current-theme color for the given palette key.
"""

import os
import tkinter as tk
from tkinter import ttk

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Sidebar background colors used by main_window.py
DARK_SIDEBAR_BG = "#181825"
LIGHT_SIDEBAR_BG = "#e6e9ef"
DARK_SEP_COLOR = "#313244"
LIGHT_SEP_COLOR = "#ccd0da"
DARK_LOGO_COLOR = "#89b4fa"
LIGHT_LOGO_COLOR = "#1e66f5"

# Module-level theme state
_is_dark = True


def is_dark_theme():
    return _is_dark


def set_theme(dark):
    global _is_dark
    _is_dark = dark


def themed(dark_val, light_val):
    """Return dark_val or light_val based on current theme."""
    return dark_val if _is_dark else light_val


# Centralized color palette
COLORS = {
    "dark": {
        "base": "#1e1e2e",
        "mantle": "#181825",
        "surface0": "#313244",
        "surface1": "#45475a",
        "surface2": "#585b70",
        "text": "#cdd6f4",
        "subtext": "#a6adc8",
        "muted": "#6c7086",
        "blue": "#89b4fa",
        "sky": "#74c7ec",
        "teal": "#94e2d5",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "peach": "#fab387",
        "red": "#f38ba8",
        "mauve": "#cba6f7",
        "lavender": "#b4befe",
        "sep": "#313244",
        "warning": "#f9e2af",
    },
    "light": {
        "base": "#eff1f5",
        "mantle": "#e6e9ef",
        "surface0": "#ccd0da",
        "surface1": "#bcc0cc",
        "surface2": "#acb0be",
        "text": "#11111b",
        "subtext": "#3c3f58",
        "muted": "#6c6f85",
        "blue": "#1e66f5",
        "sky": "#04a5e5",
        "teal": "#179299",
        "green": "#40a02b",
        "yellow": "#df8e1d",
        "peach": "#fe640b",
        "red": "#d20f39",
        "mauve": "#8839ef",
        "lavender": "#7287fd",
        "sep": "#ccd0da",
        "warning": "#d35400",
    },
}


def c(name):
    """Get a named color for the current theme."""
    palette = COLORS["dark"] if _is_dark else COLORS["light"]
    return palette.get(name, "#ff00ff")


def apply_theme(root: tk.Tk):
    """Apply the current theme to all ttk widgets via the Style object.

    Call this whenever the theme is toggled.
    """
    style = ttk.Style(root)

    # Use clam as base — it's the most customizable built-in theme
    style.theme_use("clam")

    bg = c("base")
    mantle = c("mantle")
    surface0 = c("surface0")
    surface1 = c("surface1")
    surface2 = c("surface2")
    text_color = c("text")
    subtext = c("subtext")
    muted = c("muted")
    blue = c("blue")
    green = c("green")
    red = c("red")
    yellow = c("yellow")

    # Configure default for all widgets
    style.configure(".", background=bg, foreground=text_color,
                    fieldbackground=surface0, bordercolor=surface1,
                    insertcolor=text_color,
                    font=("Segoe UI", 11))

    # TFrame
    style.configure("TFrame", background=bg)
    style.configure("Sidebar.TFrame", background=mantle)
    style.configure("Toolbar.TFrame", background=mantle)

    # TLabel
    style.configure("TLabel", background=bg, foreground=text_color)
    style.configure("Heading.TLabel", font=("Segoe UI", 18, "bold"), foreground=text_color, background=bg)
    style.configure("Subheading.TLabel", font=("Segoe UI", 12), foreground=subtext, background=bg)
    style.configure("Muted.TLabel", font=("Segoe UI", 10), foreground=muted, background=bg)
    style.configure("Sidebar.TLabel", background=mantle, foreground=text_color)
    style.configure("Toolbar.TLabel", background=mantle, foreground=text_color)
    style.configure("Logo.TLabel", background=mantle, foreground=blue,
                    font=("Consolas", 5))
    style.configure("Version.TLabel", background=mantle, foreground=muted,
                    font=("Segoe UI", 9))

    # TButton
    style.configure("TButton", background=surface0, foreground=text_color,
                    bordercolor=surface1, padding=(12, 6),
                    font=("Segoe UI", 11))
    style.map("TButton",
              background=[("active", surface1), ("disabled", bg)],
              foreground=[("disabled", muted)])

    # Primary button
    style.configure("Primary.TButton", background=blue, foreground=bg,
                    font=("Segoe UI", 11, "bold"), borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", c("sky")), ("disabled", surface1)],
              foreground=[("disabled", muted)])

    # Danger button
    style.configure("Danger.TButton", background=red, foreground=bg,
                    font=("Segoe UI", 11, "bold"), borderwidth=0)
    style.map("Danger.TButton",
              background=[("active", c("peach"))])

    # Green button
    style.configure("Green.TButton", background=green, foreground=bg,
                    font=("Segoe UI", 12, "bold"), borderwidth=0)
    style.map("Green.TButton",
              background=[("active", c("teal")), ("disabled", surface1)],
              foreground=[("disabled", muted)])

    # Mauve button
    style.configure("Mauve.TButton", background=c("mauve"), foreground=bg,
                    font=("Segoe UI", 11, "bold"), borderwidth=0)
    style.map("Mauve.TButton",
              background=[("active", c("lavender"))])

    # Peach button
    style.configure("Peach.TButton", background=c("peach"), foreground=bg,
                    font=("Segoe UI", 11, "bold"), borderwidth=0)
    style.map("Peach.TButton",
              background=[("active", yellow)])

    # Nav button (sidebar)
    style.configure("Nav.TButton", background=mantle, foreground=text_color,
                    borderwidth=0, padding=(12, 8),
                    font=("Segoe UI", 12), anchor="w")
    style.map("Nav.TButton",
              background=[("active", surface0), ("selected", surface0)],
              foreground=[("selected", blue)])

    # Active nav button
    style.configure("NavActive.TButton", background=surface0, foreground=blue,
                    borderwidth=0, padding=(12, 8),
                    font=("Segoe UI", 12, "bold"), anchor="w")

    # TEntry
    style.configure("TEntry", fieldbackground=surface0, foreground=text_color,
                    insertcolor=text_color, bordercolor=surface1, padding=4)
    style.map("TEntry",
              bordercolor=[("focus", blue)],
              fieldbackground=[("disabled", bg)])

    # TCombobox
    style.configure("TCombobox", fieldbackground=surface0, foreground=text_color,
                    bordercolor=surface1, padding=4, arrowcolor=text_color)
    style.map("TCombobox",
              bordercolor=[("focus", blue)],
              fieldbackground=[("readonly", surface0)])

    # TCheckbutton
    style.configure("TCheckbutton", background=bg, foreground=text_color,
                    indicatorcolor=surface0, indicatorrelief="flat")
    style.map("TCheckbutton",
              indicatorcolor=[("selected", blue)],
              background=[("active", bg)])

    # TRadiobutton
    style.configure("TRadiobutton", background=bg, foreground=text_color,
                    indicatorcolor=surface0, indicatorrelief="flat",
                    font=("Segoe UI", 12), padding=(6, 6))
    style.map("TRadiobutton",
              indicatorcolor=[("selected", blue)],
              background=[("active", bg)])

    # TNotebook (tab widget)
    style.configure("TNotebook", background=bg, bordercolor=surface0)
    style.configure("TNotebook.Tab", background=mantle, foreground=subtext,
                    padding=(12, 6), bordercolor=surface0)
    style.map("TNotebook.Tab",
              background=[("selected", bg)],
              foreground=[("selected", blue)])

    # Treeview (replaces QTableView)
    style.configure("Treeview", background=bg, foreground=text_color,
                    fieldbackground=bg, bordercolor=surface0,
                    rowheight=28, font=("Segoe UI", 11))
    style.configure("Treeview.Heading", background=mantle, foreground=text_color,
                    font=("Segoe UI", 11, "bold"), bordercolor=surface0)
    style.map("Treeview",
              background=[("selected", surface0)],
              foreground=[("selected", text_color)])
    style.map("Treeview.Heading",
              background=[("active", surface0)],
              foreground=[("active", blue)])

    # TProgressbar
    style.configure("TProgressbar", background=blue, troughcolor=surface0,
                    borderwidth=0)
    style.configure("Green.Horizontal.TProgressbar", background=green,
                    troughcolor=surface0, borderwidth=0)

    # TLabelframe
    style.configure("TLabelframe", background=bg, foreground=text_color,
                    bordercolor=surface0)
    style.configure("TLabelframe.Label", background=bg, foreground=text_color,
                    font=("Segoe UI", 11, "bold"))

    # TSeparator
    style.configure("TSeparator", background=surface0)

    # TSpinbox
    style.configure("TSpinbox", fieldbackground=surface0, foreground=text_color,
                    bordercolor=surface1, arrowcolor=text_color, padding=4)
    style.map("TSpinbox",
              bordercolor=[("focus", blue)])

    # Vertical.TScrollbar
    style.configure("Vertical.TScrollbar", background=surface1,
                    troughcolor=bg, borderwidth=0, arrowcolor=text_color)
    style.map("Vertical.TScrollbar",
              background=[("active", surface2)])

    # Horizontal.TScrollbar
    style.configure("Horizontal.TScrollbar", background=surface1,
                    troughcolor=bg, borderwidth=0, arrowcolor=text_color)
    style.map("Horizontal.TScrollbar",
              background=[("active", surface2)])

    # TPanedwindow
    style.configure("TPanedwindow", background=surface0)

    # Configure the root window
    root.configure(bg=bg)

    # Option database for tk widgets that don't use ttk
    root.option_add("*Background", bg)
    root.option_add("*Foreground", text_color)
    root.option_add("*Font", "TkDefaultFont")
    root.option_add("*selectBackground", blue)
    root.option_add("*selectForeground", bg)
