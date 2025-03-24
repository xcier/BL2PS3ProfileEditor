import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import subprocess
import os

CONFIG_PATH = "config.ini"
PAYLOAD_PATH = "PAYLOAD"
BASE_MAX = 9975731.0
OVERDRIVE_MAX = BASE_MAX * 2

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        # Don't recreate if already up, or if there's no text
        if self.tipwindow or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + cy + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.configure(bg="#222")
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT, background="#222",
            foreground="#eee", relief=tk.SOLID, borderwidth=1,
            font=("Segoe UI", 9), padx=5, pady=2
        )
        label.pack()

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# Main editor app
class BorderlandsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        # Hide standard window decorations
        self.overrideredirect(True)
        self.geometry("720x680")
        self.configure(bg="#1e1e1e")

        # For dragging the window
        self._offsetx = 0
        self._offsety = 0

        # Config data
        self.config_data = configparser.ConfigParser()
        self.stat_entries = {}
        self.other_entries = {}

        # Build GUI
        self.create_title_bar()
        self.create_main_content()

        # Load config
        self.load_config()

    def create_title_bar(self):
        # Title bar
        bar = tk.Frame(self, bg="#111111", height=30)
        bar.pack(fill="x", side="top")

        # Title
        title_lbl = tk.Label(
            bar, text="Borderlands 2 - Profile Editor",
            bg="#111111", fg="#f0c000", font=("Segoe UI", 12, "bold")
        )
        title_lbl.pack(side="left", padx=10, pady=2)

        # Close btn
        btn_close = tk.Button(
            bar, text="X", command=self.destroy,
            font=("Segoe UI", 10), bg="#333", fg="white", activebackground="#555",
            bd=0, width=3
        )
        btn_close.pack(side="right", padx=(0, 2))
        ToolTip(btn_close, "Close")

        # Minimize btn
        btn_min = tk.Button(
            bar, text="_", command=self.minimize_window,
            font=("Segoe UI", 10), bg="#333", fg="white", activebackground="#555",
            bd=0, width=3
        )
        btn_min.pack(side="right")
        ToolTip(btn_min, "Minimize")

        # Dragging
        bar.bind("<Button-1>", self.start_move)
        bar.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def do_move(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        self.geometry(f'+{x}+{y}')

    def minimize_window(self):
        # Turn off custom frame to allow iconify on Windows
        self.overrideredirect(False)
        self.iconify()
        # When restored, re-bind the override
        self.bind("<Map>", self.restore_window)

    def restore_window(self, event):
        self.unbind("<Map>")
        self.overrideredirect(True)

    def create_main_content(self):
        # Outer frame with scrolling
        main_frame = tk.Frame(self, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, bg="#1e1e1e", highlightthickness=0)
        scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_y.set)

        self.content_frame = tk.Frame(canvas, bg="#1e1e1e")
        self.content_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Main title
        tk.Label(
            self.content_frame,
            text="BORDERLANDS 2 PROFILE EDITOR",
            font=("Segoe UI", 20, "bold"),
            fg="#f0c000", bg="#1e1e1e"
        ).pack(pady=(15, 10))

        # Stats
        stats_section = tk.LabelFrame(
            self.content_frame, text="Badass Rank Stats", fg="white", bg="#1e1e1e",
            font=("Segoe UI", 12, "bold"), bd=2
        )
        stats_section.pack(padx=20, pady=10, fill="x")

        self.bar_stats_frame = tk.Frame(stats_section, bg="#1e1e1e")
        self.bar_stats_frame.pack(fill="x", padx=10, pady=8)

        # Misc settings
        misc_section = tk.LabelFrame(
            self.content_frame, text="System Settings", fg="white", bg="#1e1e1e",
            font=("Segoe UI", 12, "bold"), bd=2
        )
        misc_section.pack(padx=20, pady=10, fill="x")

        self.misc_frame = tk.Frame(misc_section, bg="#1e1e1e")
        self.misc_frame.pack(fill="x", padx=10, pady=8)

        # Profile Ops
        ops_section = tk.LabelFrame(
            self.content_frame, text="Profile Operations", fg="white", bg="#1e1e1e",
            font=("Segoe UI", 12, "bold"), bd=2
        )
        ops_section.pack(padx=20, pady=10, fill="x")

        self.update_button = tk.Button(
            ops_section, text="Update Payload (Auto-Saves)",
            command=self.update_payload, bg="#f0c000", fg="#000",
            activebackground="#ffdd55", font=("Segoe UI", 11, "bold"), width=30
        )
        self.update_button.pack(pady=10)

        # Status
        self.status_label = tk.Label(
            self.content_frame, text="", font=("Segoe UI", 10),
            fg="lime", bg="#1e1e1e"
        )
        self.status_label.pack(pady=(5, 10))

    def load_config(self):
        self.config_data.read(CONFIG_PATH)

        # BarStats
        if 'BarStats' in self.config_data:
            stats = list(self.config_data['BarStats'].items())
            for i, (stat, val) in enumerate(stats):
                r, c = divmod(i, 2)
                f = tk.Frame(self.bar_stats_frame, bg="#1e1e1e")
                f.grid(row=r, column=c, sticky="w", padx=10, pady=5)

                lbl = tk.Label(
                    f, text=stat + ":", width=16, anchor="w",
                    bg="#1e1e1e", fg="#eee", font=("Segoe UI", 10, "bold")
                )
                lbl.pack(side="left")

                e = tk.Entry(
                    f, width=12, bg="#333", fg="#f0c000",
                    insertbackground="white", justify="right", font=("Segoe UI", 10)
                )
                e.insert(0, val)
                e.pack(side="left")

                self.stat_entries[stat] = e
                self.add_tooltip(e, True)

        # Other sections
        rows = [
            [("GoldenKeys", "count"), ("FOV", "value")],
            [("BarTokens", "count"), ("BarRank", "value")]
        ]
        for row_data in rows:
            row_frame = tk.Frame(self.misc_frame, bg="#1e1e1e")
            row_frame.pack(fill="x", pady=5)

            for section, key in row_data:
                if section in self.config_data and key in self.config_data[section]:
                    inner = tk.Frame(row_frame, bg="#1e1e1e")
                    inner.pack(side="left", padx=10, expand=True)

                    lbl = tk.Label(
                        inner, text=section + ":",
                        width=14, anchor="w", bg="#1e1e1e",
                        fg="#eee", font=("Segoe UI", 10, "bold")
                    )
                    lbl.pack(side="left")

                    e = tk.Entry(
                        inner, width=12, bg="#333", fg="#f0c000",
                        insertbackground="white", justify="right", font=("Segoe UI", 10)
                    )
                    e.insert(0, self.config_data[section][key])
                    e.pack(side="left", fill="x")

                    self.other_entries[(section, key)] = e

    def add_tooltip(self, widget, is_stat=False):
        if is_stat:
            tip = (
                f"Base Max: {BASE_MAX:,.1f}\n"
                f"Overdrive Max: {OVERDRIVE_MAX:,.1f}\n"
                "Allowed up to Overdrive Max."
            )
        else:
            tip = "Enter a value"
        ToolTip(widget, tip)

    def save_config(self):
        # Make sure BarStats section exists
        if 'BarStats' not in self.config_data:
            self.config_data.add_section('BarStats')

        # Save stats
        for stat, entry in self.stat_entries.items():
            try:
                val = float(entry.get())
                val = min(val, OVERDRIVE_MAX)
                entry.delete(0, tk.END)
                entry.insert(0, str(val))
                self.config_data['BarStats'][stat] = str(val)
            except ValueError:
                pass

        # Save other stuff
        for (section, key), entry in self.other_entries.items():
            if section not in self.config_data:
                self.config_data.add_section(section)
            self.config_data[section][key] = entry.get()

        # Write to file
        with open(CONFIG_PATH, 'w') as f:
            self.config_data.write(f)
            f.flush()
            os.fsync(f.fileno())

    def update_payload(self):
        self.save_config()
        if not os.path.exists(PAYLOAD_PATH):
            messagebox.showerror("Error", f"PAYLOAD not found:\n{PAYLOAD_PATH}")
            return
        try:
            subprocess.run(
                ["python", "update_payload.py", "-c", CONFIG_PATH, "-p", PAYLOAD_PATH],
                check=True
            )
            self.status_label.config(text="Payload updated successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Payload update failed:\n{e}")

if __name__ == "__main__":
    app = BorderlandsEditor()
    app.mainloop()
