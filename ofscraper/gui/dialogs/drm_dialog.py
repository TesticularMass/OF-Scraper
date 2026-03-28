import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ofscraper.gui.signals import app_signals
from ofscraper.gui.styles import c
from ofscraper.gui.widgets.styled_button import StyledButton

log = logging.getLogger("shared")

# Bundled script location: ofscraper/gui/scripts/drm_keydive.py
_BUNDLED_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "drm_keydive.py")
_BUNDLED_SCRIPT = os.path.normpath(_BUNDLED_SCRIPT)

_REQUIREMENTS_TEXT = """\
SYSTEM REQUIREMENTS
───────────────────
  OS:       Windows 10/11  OR  Debian-based Linux (Ubuntu 20.04+, KDE Neon, PikaOS)
            macOS is NOT supported.
  CPU:      x86-64 processor
  RAM:      8 GB minimum (16 GB recommended)
  Disk:     8 GB free space (SDK + emulator image + APKs)
  Internet: Required — downloads ~3 GB of tools on first run

  Hardware virtualization (VT-x / KVM) is strongly recommended.
  Without it the script falls back to software emulation which may
  take 45–90 minutes instead of 10–20 minutes.

REQUIRED PYTHON PACKAGES
────────────────────────
  pip install requests

  Only the 'requests' package needs to be installed manually.
  frida, frida-tools, and all other dependencies (Android SDK,
  JDK 17, Frida server, KeyDive, Kaltura APK) are downloaded
  and installed automatically by the script on first run.

OUTPUT FILES
────────────
  client_id.bin    — Widevine client identification blob
  private_key.pem  — Widevine device private key

  After successful extraction you will be offered the option to
  save these paths to config.json and set Key Mode to "manual".\
"""


class _ScriptRunner:
    """Runs drm_keydive.py in a subprocess and streams output line by line."""

    def __init__(self, script_path, output_dir, on_line, on_finished, root):
        self.script_path = script_path
        self.output_dir = output_dir
        self._on_line = on_line
        self._on_finished = on_finished
        self._root = root

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        cmd = [sys.executable, self.script_path, "--out-dir", self.output_dir]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                cwd=os.path.dirname(self.script_path),
            )
            for line in proc.stdout:
                stripped = line.rstrip()
                try:
                    self._root.after(0, self._on_line, stripped)
                except Exception:
                    pass
            proc.wait()
            try:
                self._root.after(0, self._on_finished, proc.returncode)
            except Exception:
                pass
        except Exception as e:
            try:
                self._root.after(0, self._on_line, f"ERROR launching script: {e}")
                self._root.after(0, self._on_finished, 1)
            except Exception:
                pass


class DRMKeyPage(ttk.Frame):
    """DRM Key Creation page -- runs drm_keydive.py and optionally updates config.json."""

    def __init__(self, parent, manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.manager = manager
        self._runner = None
        self._last_output_dir = None
        self._setup_ui()
        self._try_prefill_script()

    def _get_root(self):
        """Return the tkinter root window."""
        return self.winfo_toplevel()

    def _try_prefill_script(self):
        """Pre-fill the script path with the bundled script if it exists."""
        if os.path.isfile(_BUNDLED_SCRIPT):
            self.script_input.delete(0, tk.END)
            self.script_input.insert(0, _BUNDLED_SCRIPT)

    def _setup_ui(self):
        # Scrollable container using canvas
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        self._scroll_frame = ttk.Frame(canvas)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel to canvas (scoped to enter/leave)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        container = self._scroll_frame
        pad_x = 40
        pad_y = 10

        # -- Header --
        header = ttk.Label(container, text="DRM Key Creation",
                           style="Heading.TLabel")
        header.pack(anchor="w", padx=pad_x, pady=(pad_y * 2, 4))

        subtitle = ttk.Label(
            container,
            text="Generate Widevine L3 keys using an Android emulator. "
                 "Produces client_id.bin and private_key.pem for use with OF-Scraper.",
            style="Subheading.TLabel",
            wraplength=700,
        )
        subtitle.pack(anchor="w", padx=pad_x, pady=(0, pad_y))

        # -- Requirements box --
        req_frame = ttk.LabelFrame(container, text="Requirements & Information")
        req_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        req_body = tk.Text(req_frame, wrap=tk.NONE, height=18, font=("Consolas", 9),
                           relief=tk.FLAT, borderwidth=0)
        req_body.insert(tk.END, _REQUIREMENTS_TEXT)
        req_body.configure(state=tk.DISABLED)
        req_body.pack(fill=tk.X, padx=12, pady=8)

        # -- Script path --
        script_frame = ttk.Frame(container)
        script_frame.pack(fill=tk.X, padx=pad_x, pady=(pad_y, 4))

        script_lbl = ttk.Label(script_frame, text="Extraction Script:", width=18)
        script_lbl.pack(side=tk.LEFT)

        self.script_input = ttk.Entry(script_frame)
        self.script_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))

        script_browse = StyledButton(script_frame, text="Browse",
                                     command=self._browse_script)
        script_browse.pack(side=tk.LEFT)

        # -- Output directory --
        out_frame = ttk.Frame(container)
        out_frame.pack(fill=tk.X, padx=pad_x, pady=(4, pad_y))

        out_lbl = ttk.Label(out_frame, text="Output Folder:", width=18)
        out_lbl.pack(side=tk.LEFT)

        self.output_input = ttk.Entry(out_frame)
        self.output_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))

        out_browse = StyledButton(out_frame, text="Browse",
                                  command=self._browse_output)
        out_browse.pack(side=tk.LEFT)

        # -- Warning --
        self._warning_label = ttk.Label(
            container,
            text="WARNING: First run downloads ~3 GB of tools and may take 45-90 min "
                 "on systems without hardware virtualization (VT-x / KVM).",
            wraplength=700,
            font=("Segoe UI", 11, "bold"),
            foreground=c("warning"),
        )
        self._warning_label.pack(anchor="w", padx=pad_x, pady=pad_y)

        app_signals.theme_changed.connect(self._apply_theme)

        # -- Generate button --
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, padx=pad_x, pady=pad_y)

        self.generate_btn = StyledButton(btn_frame, text="Generate Keys",
                                         primary=True, command=self._on_generate)
        self.generate_btn.pack(side=tk.RIGHT)

        # -- Live output log --
        self.output_text = tk.Text(container, wrap=tk.WORD, height=18,
                                   font=("Consolas", 9), state=tk.DISABLED,
                                   relief=tk.SUNKEN, borderwidth=1)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=pad_x, pady=(pad_y, pad_y * 2))

    def _apply_theme(self, _is_dark=True):
        self._warning_label.configure(foreground=c("warning"))

    def _browse_script(self):
        path = filedialog.askopenfilename(
            title="Select Extraction Script",
            filetypes=[("Python Scripts", "*.py"), ("All Files", "*.*")],
        )
        if path:
            self.script_input.delete(0, tk.END)
            self.script_input.insert(0, path)

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_input.delete(0, tk.END)
            self.output_input.insert(0, folder)

    def _on_generate(self):
        script = self.script_input.get().strip()
        if not script:
            messagebox.showwarning(
                "Missing",
                "No extraction script path set.\n"
                "The bundled script was not found -- please browse to drm_keydive.py.",
            )
            return
        if not os.path.isfile(script):
            messagebox.showwarning("Not Found", f"Script not found:\n{script}")
            return

        # Use typed path or fall back to the script's own default
        output_dir = self.output_input.get().strip()
        if not output_dir:
            output_dir = os.path.normpath(os.path.expanduser("~/.config/ofscraper/device"))

        os.makedirs(output_dir, exist_ok=True)
        self._last_output_dir = output_dir

        self._text_clear()
        self._text_append(f"Starting DRM key extraction...\nOutput directory: {output_dir}\n")
        self.generate_btn.configure(state=tk.DISABLED)
        app_signals.status_message.emit("DRM key extraction in progress...")

        self._runner = _ScriptRunner(
            script, output_dir, self._on_line, self._on_finished, self._get_root()
        )
        self._runner.start()

    def _text_clear(self):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _text_append(self, text):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _on_line(self, line):
        self._text_append(line)

    def _on_finished(self, exit_code):
        self.generate_btn.configure(state=tk.NORMAL)
        if exit_code == 0:
            self._text_append("\nKey extraction completed successfully.")
            app_signals.status_message.emit("DRM key extraction complete")
            self._offer_config_update()
        else:
            self._text_append(f"\nScript exited with code {exit_code}.")
            app_signals.status_message.emit("DRM key extraction failed")
            messagebox.showerror(
                "Extraction Failed",
                f"The extraction script exited with code {exit_code}.\n"
                "Check the output log for details.",
            )

    def _offer_config_update(self):
        if not self._last_output_dir:
            return

        client_id = os.path.join(self._last_output_dir, "client_id.bin")
        private_key = os.path.join(self._last_output_dir, "private_key.pem")

        missing = [p for p in (client_id, private_key) if not os.path.isfile(p)]
        if missing:
            messagebox.showwarning(
                "Key Files Not Found",
                "Extraction reported success but the key files were not found:\n"
                + "\n".join(missing)
                + "\n\nConfig was not updated.",
            )
            return

        reply = messagebox.askyesno(
            "Update Configuration",
            "Keys were saved successfully!\n\n"
            f"  Client ID:   {client_id}\n"
            f"  Private Key: {private_key}\n\n"
            "Would you like to update config.json with these paths\n"
            "and set Key Mode to manual?",
        )
        if not reply:
            return

        try:
            self._update_config(client_id, private_key)
            app_signals.config_updated.emit()
            messagebox.showinfo(
                "Config Updated",
                "config.json has been updated:\n"
                "  - key-mode-default -> manual\n"
                f"  - client-id -> {client_id}\n"
                f"  - private-key -> {private_key}",
            )
            app_signals.status_message.emit("Config updated with DRM keys")
        except Exception as e:
            log.debug(f"Config update failed: {e}", exc_info=True)
            messagebox.showerror("Config Update Failed",
                                 f"Could not update config.json:\n{e}")

    def _update_config(self, client_id, private_key):
        from ofscraper.utils.config.file import open_config, write_config
        import ofscraper.utils.config.config as config_module

        config = open_config()
        cdm = config.setdefault("cdm_options", {})
        cdm["key-mode-default"] = "manual"
        cdm["client-id"] = client_id
        cdm["private-key"] = private_key
        write_config(config)
        # Clear the module-level cache so the next read_config() call re-reads the file
        config_module.config = None
