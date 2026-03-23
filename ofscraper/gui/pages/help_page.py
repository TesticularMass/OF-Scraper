import logging
import re
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c

log = logging.getLogger("shared")

DISCORD_HELP_URL = "https://discord.gg/wN7uxEVHRK"

_RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_CODE = re.compile(r"`([^`]+)`")


class HelpPage(ttk.Frame):
    """In-app README / help page for the GUI."""

    def __init__(self, parent=None, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._anchor_marks = {}  # anchor_id -> text mark name
        self._link_ranges = []   # (tag_name, url) for click handling
        self._setup_ui()
        self._load_help_text()
        app_signals.theme_changed.connect(lambda _: self._load_help_text())

    def _setup_ui(self):
        pad = ttk.Frame(self)
        pad.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        header = ttk.Label(pad, text="Help / README", style="Heading.TLabel")
        header.pack(anchor=tk.W)

        subtitle = ttk.Label(
            pad,
            text="Quick guide to the OF-Scraper GUI: what each section does and how to use it.",
            style="Subheading.TLabel",
            wraplength=800,
        )
        subtitle.pack(anchor=tk.W, pady=(0, 12))

        # Actions row
        actions_frame = ttk.Frame(pad)
        actions_frame.pack(fill=tk.X, pady=(0, 12))

        self._jump_var = tk.StringVar(value="Jump to\u2026")
        jump_values = [
            "Jump to\u2026",
            "Left navigation",
            "Scraper workflow",
            "Select Content Areas & Filters",
            "Select Models",
            "Configuration (config.json)",
            "Table / Scraping page",
            "Filters",
            "Table columns",
            "Merge DBs",
            "Troubleshooting notes",
            "Auth Issues",
        ]
        self._jump_anchors = {
            "Left navigation": "nav-left",
            "Scraper workflow": "scraper-workflow",
            "Select Content Areas & Filters": "sca-root",
            "Select Models": "models-root",
            "Configuration (config.json)": "config-root",
            "Table / Scraping page": "table-root",
            "Filters": "filters-root",
            "Table columns": "table-columns",
            "Merge DBs": "merge-dbs",
            "Troubleshooting notes": "troubleshooting",
            "Auth Issues": "auth-issues",
        }
        self.jump_combo = ttk.Combobox(actions_frame, textvariable=self._jump_var,
                                        values=jump_values, state="readonly",
                                        width=40)
        self.jump_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.jump_combo.bind("<<ComboboxSelected>>", self._on_jump_changed)

        additional_btn = ttk.Button(actions_frame, text="Additional Help",
                                     command=self._on_additional_help)
        additional_btn.pack(side=tk.RIGHT, padx=(4, 0))

        reload_btn = ttk.Button(actions_frame, text="Reload Help",
                                 command=self._load_help_text)
        reload_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # Text viewer
        viewer_frame = ttk.Frame(pad)
        viewer_frame.pack(fill=tk.BOTH, expand=True)
        viewer_frame.columnconfigure(0, weight=1)
        viewer_frame.rowconfigure(0, weight=1)

        self.viewer = tk.Text(
            viewer_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            bg=c("base"),
            fg=c("text"),
            insertbackground=c("text"),
            selectbackground=c("blue"),
            selectforeground=c("base"),
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=c("surface0"),
            highlightcolor=c("blue"),
            padx=16,
            pady=12,
            cursor="arrow",
        )
        self.viewer.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL,
                                   command=self.viewer.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.viewer.configure(yscrollcommand=scrollbar.set)

        self._configure_tags()

    def _configure_tags(self):
        """Set up text tags for markdown formatting."""
        self.viewer.tag_configure("h2", font=("Segoe UI", 18, "bold"),
                                  foreground=c("green"), spacing1=18, spacing3=8)
        self.viewer.tag_configure("h3", font=("Segoe UI", 15, "bold"),
                                  foreground=c("green"), spacing1=14, spacing3=6)
        self.viewer.tag_configure("h4", font=("Segoe UI", 13, "bold"),
                                  foreground=c("green"), spacing1=10, spacing3=4)
        self.viewer.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.viewer.tag_configure("code", font=("Consolas", 11),
                                  background=c("mantle"), foreground=c("text"))
        self.viewer.tag_configure("bullet", lmargin1=20, lmargin2=32)
        self.viewer.tag_configure("bullet2", lmargin1=40, lmargin2=52)
        self.viewer.tag_configure("hr", foreground=c("surface1"),
                                  font=("Consolas", 6), spacing1=8, spacing3=8)
        self.viewer.tag_configure("normal", font=("Segoe UI", 11),
                                  spacing1=2, spacing3=2)

    def _on_jump_changed(self, event=None):
        sel = self._jump_var.get()
        anchor = self._jump_anchors.get(sel)
        if anchor:
            self.scroll_to_anchor(anchor)
        self._jump_var.set("Jump to\u2026")

    def _on_additional_help(self):
        if messagebox.askyesno(
            "Additional Help",
            f"For additional help join our discord {DISCORD_HELP_URL}\n\n"
            "Open Discord invite in your browser?",
        ):
            try:
                webbrowser.open(DISCORD_HELP_URL)
            except Exception:
                pass

    def _help_md_path(self):
        return Path(__file__).resolve().parents[1] / "help" / "GUI_HELP.md"

    def scroll_to_anchor(self, anchor):
        """Scroll the viewer to an internal anchor."""
        anchor = (anchor or "").strip().lstrip("#")
        if not anchor:
            return
        mark = self._anchor_marks.get(anchor)
        if mark:
            self.viewer.see(mark)

    def _insert_inline(self, line, extra_tags=()):
        """Parse inline markdown (bold, code, links) and insert into the text widget."""
        # Split line into segments: bold, code, links, and plain text
        # Process in order: find all matches, sort by position, insert segments
        segments = []  # (start, end, type, data)

        for m in _RE_LINK.finditer(line):
            segments.append((m.start(), m.end(), "link", (m.group(1), m.group(2))))
        for m in _RE_BOLD.finditer(line):
            # Don't add bold if it overlaps with a link
            if not any(s[0] <= m.start() < s[1] for s in segments):
                segments.append((m.start(), m.end(), "bold", m.group(1)))
        for m in _RE_CODE.finditer(line):
            if not any(s[0] <= m.start() < s[1] for s in segments):
                segments.append((m.start(), m.end(), "code", m.group(1)))

        segments.sort(key=lambda s: s[0])

        pos = 0
        for start, end, seg_type, data in segments:
            # Insert plain text before this segment
            if start > pos:
                self.viewer.insert(tk.END, line[pos:start], tuple(extra_tags) + ("normal",) if extra_tags else ("normal",))

            if seg_type == "link":
                link_text, url = data
                tag_name = f"link_{len(self._link_ranges)}"
                self.viewer.tag_configure(tag_name, foreground=c("blue"),
                                           underline=True)
                self.viewer.tag_bind(tag_name, "<Button-1>",
                                      lambda e, u=url: self._handle_href(u))
                self.viewer.tag_bind(tag_name, "<Enter>",
                                      lambda e: self.viewer.configure(cursor="hand2"))
                self.viewer.tag_bind(tag_name, "<Leave>",
                                      lambda e: self.viewer.configure(cursor="arrow"))
                self._link_ranges.append((tag_name, url))
                tags = tuple(extra_tags) + (tag_name,) if extra_tags else (tag_name,)
                self.viewer.insert(tk.END, link_text, tags)
            elif seg_type == "bold":
                tags = tuple(extra_tags) + ("bold",) if extra_tags else ("bold",)
                self.viewer.insert(tk.END, data, tags)
            elif seg_type == "code":
                tags = tuple(extra_tags) + ("code",) if extra_tags else ("code",)
                self.viewer.insert(tk.END, data, tags)

            pos = end

        # Insert remaining plain text
        if pos < len(line):
            tags = tuple(extra_tags) + ("normal",) if extra_tags else ("normal",)
            self.viewer.insert(tk.END, line[pos:], tags)

    def _handle_href(self, href):
        href = (href or "").strip()
        if not href:
            return
        if href.startswith("#"):
            self.scroll_to_anchor(href[1:])
        else:
            try:
                webbrowser.open(href)
            except Exception:
                pass

    def _load_help_text(self):
        md = None
        p = self._help_md_path()
        try:
            if p.exists():
                md = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            log.debug(f"Failed reading help markdown: {e}")

        if not md:
            md = _FALLBACK_HELP_MD

        self._render_markdown(md)

    def _render_markdown(self, md):
        """Render markdown content into the tk.Text widget with tags."""
        self.viewer.configure(state=tk.NORMAL)
        self.viewer.delete("1.0", tk.END)
        self._anchor_marks.clear()
        self._link_ranges.clear()

        lines = (md or "").splitlines()
        pending_anchor = None

        for raw in lines:
            line = raw.rstrip()

            # Buffer <a id="..."> anchor lines
            if line.strip().startswith("<a ") and line.strip().endswith("</a>"):
                id_match = re.search(
                    r'id=[\"\'\u201c\u201d]([^\"\'\u201c\u201d]+)[\"\'\u201c\u201d]',
                    line.strip()
                )
                if id_match:
                    pending_anchor = id_match.group(1)
                continue

            # Horizontal rules
            if line.strip() == "---":
                if pending_anchor:
                    mark = f"anchor_{pending_anchor}"
                    self.viewer.mark_set(mark, tk.END)
                    self.viewer.mark_gravity(mark, tk.LEFT)
                    self._anchor_marks[pending_anchor] = mark
                    pending_anchor = None
                self.viewer.insert(tk.END, "\u2500" * 80 + "\n", "hr")
                continue

            # Headings
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                # Strip inline markdown for heading display
                text = _RE_LINK.sub(r"\1", text)
                text = _RE_BOLD.sub(r"\1", text)
                text = _RE_CODE.sub(r"\1", text)

                h_tag = f"h{min(max(level + 1, 2), 4)}"

                if pending_anchor:
                    mark = f"anchor_{pending_anchor}"
                    self.viewer.mark_set(mark, tk.END)
                    self.viewer.mark_gravity(mark, tk.LEFT)
                    self._anchor_marks[pending_anchor] = mark
                    pending_anchor = None

                self.viewer.insert(tk.END, text + "\n", h_tag)
                continue

            # Blank lines
            if not line.strip():
                self.viewer.insert(tk.END, "\n")
                continue

            # List items
            lm = re.match(r"^(\s*)-\s+(.*)$", line)
            if lm:
                indent = len(lm.group(1).replace("\t", "  "))
                bullet_tag = "bullet2" if indent >= 2 else "bullet"
                self.viewer.insert(tk.END, "\u2022 ", bullet_tag)
                self._insert_inline(lm.group(2).strip(), extra_tags=(bullet_tag,))
                self.viewer.insert(tk.END, "\n")
                continue

            # Flush pending anchor before paragraph text
            if pending_anchor:
                mark = f"anchor_{pending_anchor}"
                self.viewer.mark_set(mark, tk.END)
                self.viewer.mark_gravity(mark, tk.LEFT)
                self._anchor_marks[pending_anchor] = mark
                pending_anchor = None

            # Normal paragraph text
            self._insert_inline(line.strip())
            self.viewer.insert(tk.END, "\n")

        # Flush any remaining anchor
        if pending_anchor:
            mark = f"anchor_{pending_anchor}"
            self.viewer.mark_set(mark, tk.END)
            self.viewer.mark_gravity(mark, tk.LEFT)
            self._anchor_marks[pending_anchor] = mark

        self.viewer.configure(state=tk.DISABLED)

    def update_theme(self):
        """Re-apply theme colors."""
        self.viewer.configure(
            bg=c("base"),
            fg=c("text"),
            highlightbackground=c("surface0"),
            highlightcolor=c("blue"),
            selectbackground=c("blue"),
            selectforeground=c("base"),
        )
        self._configure_tags()


_FALLBACK_HELP_MD = """\
# OF-Scraper GUI Help / README

This page explains what each section of the GUI does and how to use it.

## Left navigation

- **Scraper**: Main workflow for downloading/liking content.
- **Authentication**: Enter your cookies/headers (stored in your profile `auth.json`).
- **Configuration**: Edit `config.json` settings (save location, formats, performance, etc.).
- **Profiles**: Manage profiles (each profile has separate auth + `.data`).
- **Merge DBs**: Merge `user_data.db` files into a single database.

## Scraper workflow (Scraper →)

### 1) Select Action
Choose what you want to do:

- **Download content from a user**: Scrape content and build the table.
- **Like / Unlike**: Perform like/unlike actions on supported areas.
- **Download + Like / Unlike**: Do both.

### 2) Select Content Areas & Filters

#### Content Areas
These are the sources to scan (depending on action):

- **Profile, Timeline, Pinned, Archived, Highlights, Stories, Messages, Purchased, Streams, Labels**

#### Additional Options
- **Scrape entire paid page (slower but more comprehensive)**: Tries harder to enumerate paid items (may be slower).
- **Scrape labels**: Pull content via labels when available.

#### Advanced Scrape Options
- **Allow duplicates (do NOT skip duplicates; treat reposts as new items)**: Disables duplicate-skipping logic.
- **Rescrape everything (ignore cache / scan from the beginning)**: Forces a full history scan.
  - **Delete model DB before scraping (resets downloaded/unlocked history)**: Deletes the model DB folder so the run starts "fresh".
  - **Also delete existing downloaded files for selected models**: Removes downloaded files under your save location for that model.

#### Daemon Mode (Auto-Repeat Scraping)
- **Enable daemon mode**: Automatically re-runs scraping on an interval.
- **Interval**: Minutes between runs.
- Optional notification/sound toggles.

#### Filters (on this page)
This page contains an embedded version of the same filter panel used on the table page.

### 3) Select Models
Search and select creators to process.

Tips:
- Use the search box (supports comma-separated values).
- Use **Select All / Deselect All / Toggle** to bulk change.

### 4) Scraping / Table page

#### Toolbar buttons
- **Filters**: Show/hide the filter sidebar.
- **Reset**: Reset filters.
- **Apply Filters**: Apply the current filter state.
- **Start Scraping >>**: Begin scraping the selected areas/models.
- **New Scrape**: Return to the first step for a new run.
- **Stop Daemon**: Stops daemon mode if enabled.
- **Select All / Deselect All**: Controls the download cart selection.
- **>> Send Downloads**: Queues selected rows for downloading.

#### Table basics
- Click a cell in **Download Cart** to toggle adding/removing it.
- Right-click any cell to filter by that value.
- Click headers to sort.

#### Progress + logs
- The **overall progress bar** is shown in the footer at the bottom of the table page.
- The console area shows detailed logs and trace output.

#### "Unlocked" column meanings (important)

The **Unlocked** column is not a direct 1:1 match with "purchased".

- **Locked**: Not viewable (paywalled).
- **Preview**: Viewable teaser/preview media for a priced item.
- **Included**: Viewable media inside a priced message **without purchasing** (e.g., teaser media that OnlyFans still marks as viewable even though the message is priced).
- **True**: Treated as fully unlocked/accessible (typically purchased / opened content).

## Filters panel (Table page)

- **Text Search**: Regex/substring search (toggle **Full string match**).
- **Media Type**: Audios / Images / Videos.
- **Response Type**: Pinned / Archived / Timeline / Stories / Highlights / Streams.
- **Status**
  - **Downloaded**: True / False / No (Paid)
  - **Unlocked**: True / False / Locked
- **Post Date Range**, **Duration (Length)**, **Price Range**, **ID Filters**, **Username**

## Merge DBs

1. Pick a **Source Folder** that contains one or more `user_data.db` files.
2. Pick a **Destination** folder for the merged output.
3. Click **Start Merge** (back up first).

## Common troubleshooting

- If a purge option deletes files/DB and you immediately start a download scrape, the scraper may recreate folders/databases right away.
- "Unlocked" values can include non-purchased viewable media depending on the source type (messages/PPV behavior differs from timeline posts).
"""
