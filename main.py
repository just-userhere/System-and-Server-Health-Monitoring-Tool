"""ServerPulse dashboard — Tkinter GUI and application startup.

How it works:
  1. psutil (via monitor.py) collects system metrics.
  2. alerts.py classifies each metric and computes overall health.
  3. Tkinter displays everything and refreshes with `after()`
     (non-blocking, so the UI stays responsive).
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

import config
import monitor
from alerts import (
    OVERALL_COLORS,
    STATUS_COLORS,
    classify_metric,
    overall_health,
)

BG = "#0f172a"
CARD_BG = "#1e293b"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"


def pct_text(value):
    return "N/A" if value is None else f"{value:.1f}%"


class MetricCard(tk.Frame):
    """A single metric card with big value, bar and status pill."""

    def __init__(self, parent, title):
        super().__init__(parent, bg=CARD_BG, padx=16, pady=14)
        self.title_label = tk.Label(
            self, text=title, bg=CARD_BG, fg=MUTED,
            font=("Segoe UI", 10, "bold"),
        )
        self.title_label.pack(anchor="w")
        self.value_label = tk.Label(
            self, text="--", bg=CARD_BG, fg=TEXT,
            font=("Segoe UI", 26, "bold"),
        )
        self.value_label.pack(anchor="w", pady=(2, 4))
        self.bar = tk.Canvas(self, height=10, bg="#334155",
                             highlightthickness=0, bd=0)
        self.bar.pack(fill="x", pady=(0, 8))
        self.status_label = tk.Label(
            self, text="...", bg="#334155", fg=TEXT,
            font=("Segoe UI", 9, "bold"), padx=10, pady=2,
        )
        self.status_label.pack(anchor="w")
        self.detail_label = tk.Label(
            self, text="", bg=CARD_BG, fg=MUTED,
            font=("Segoe UI", 9), justify="left",
        )
        self.detail_label.pack(anchor="w", pady=(8, 0))

    def update(self, percent, detail=""):
        self.value_label.config(text=pct_text(percent))
        status = classify_metric(percent)
        color = STATUS_COLORS.get(status, STATUS_COLORS["UNKNOWN"])
        label = status if status != "UNKNOWN" else "N/A"
        self.status_label.config(text=f"● {label}", fg=color)
        self.detail_label.config(text=detail)
        self.bar.delete("all")
        self.bar.update_idletasks()
        width = max(self.bar.winfo_width(), 200)
        frac = 0.0 if percent is None else max(0.0, min(float(percent), 100.0)) / 100.0
        self.bar.create_rectangle(0, 0, width * frac, 10, fill=color, outline="")


class ServerPulseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ServerPulse — System & Server Health Monitoring Tool")
        self.root.configure(bg=BG)
        self.root.geometry("980x760")
        self.root.minsize(860, 700)

        self.net_tracker = monitor.NetworkTracker()
        self.cpu_history = []
        self.auto_refresh = tk.BooleanVar(value=True)

        self._build_layout()
        # Prime psutil's non-blocking CPU counter, then start the loop.
        monitor.get_cpu_usage(interval=None)
        self.root.after(300, self.refresh)

    # ---- layout ----
    def _build_layout(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(header, text="SERVERPULSE", bg=BG, fg=TEXT,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(header, text="System & Server Health Monitoring Tool",
                 bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w")

        self.overall_banner = tk.Label(
            self.root, text="Overall Status: ...",
            bg=CARD_BG, fg=TEXT, font=("Segoe UI", 12, "bold"),
            padx=14, pady=10,
        )
        self.overall_banner.pack(fill="x", padx=20, pady=10)

        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=20)
        for col in range(3):
            cards.columnconfigure(col, weight=1, uniform="metrics")
        self.cpu_card = MetricCard(cards, "CPU")
        self.ram_card = MetricCard(cards, "RAM")
        self.disk_card = MetricCard(cards, "DISK")
        self.cpu_card.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.ram_card.grid(row=0, column=1, sticky="ew", padx=6)
        self.disk_card.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        mid = tk.Frame(self.root, bg=BG)
        mid.pack(fill="x", padx=20, pady=10)
        mid.columnconfigure(0, weight=1, uniform="mid")
        mid.columnconfigure(1, weight=1, uniform="mid")

        net_frame = tk.Frame(mid, bg=CARD_BG, padx=16, pady=12)
        net_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Label(net_frame, text="NETWORK", bg=CARD_BG, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.net_rate_label = tk.Label(net_frame, bg=CARD_BG, fg=TEXT,
                                       font=("Segoe UI", 11), justify="left")
        self.net_rate_label.pack(anchor="w", pady=(6, 0))
        self.net_total_label = tk.Label(net_frame, bg=CARD_BG, fg=MUTED,
                                        font=("Segoe UI", 9), justify="left")
        self.net_total_label.pack(anchor="w")

        graph_frame = tk.Frame(mid, bg=CARD_BG, padx=16, pady=12)
        graph_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        tk.Label(graph_frame, text="CPU HISTORY (last 60 samples)",
                 bg=CARD_BG, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.graph = tk.Canvas(graph_frame, height=86, bg="#0b1220",
                               highlightthickness=0, bd=0)
        self.graph.pack(fill="x", pady=(6, 0))

        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        bottom.columnconfigure(0, weight=1, uniform="bottom")
        bottom.columnconfigure(1, weight=1, uniform="bottom")

        sys_frame = tk.Frame(bottom, bg=CARD_BG, padx=16, pady=12)
        sys_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        tk.Label(sys_frame, text="SYSTEM INFORMATION", bg=CARD_BG, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.sys_label = tk.Label(sys_frame, bg=CARD_BG, fg=TEXT,
                                  font=("Segoe UI", 10), justify="left",
                                  anchor="w")
        self.sys_label.pack(anchor="w", pady=(6, 0))

        proc_frame = tk.Frame(bottom, bg=CARD_BG, padx=16, pady=12)
        proc_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        tk.Label(proc_frame, text="TOP PROCESSES", bg=CARD_BG, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.proc_label = tk.Label(proc_frame, bg=CARD_BG, fg=TEXT,
                                   font=("Consolas", 9), justify="left",
                                   anchor="w")
        self.proc_label.pack(anchor="w", pady=(6, 0))

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=20, pady=(4, 14))
        self.updated_label = tk.Label(footer, text="Last Updated: --",
                                      bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.updated_label.pack(side="left")
        ttk.Checkbutton(footer, text="Auto refresh",
                        variable=self.auto_refresh).pack(side="right", padx=(8, 0))
        tk.Button(footer, text="Refresh Now", command=self.refresh,
                  bg=ACCENT, fg="#0f172a", relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=14, pady=4).pack(side="right")

    # ---- refresh loop (non-blocking via after) ----
    def refresh(self):
        try:
            self._update_once()
        except Exception as exc:  # never let one bad sample kill the loop
            self.updated_label.config(text=f"Last update failed: {exc}")
        if self.auto_refresh.get():
            self.root.after(config.REFRESH_INTERVAL_MS, self.refresh)

    def _update_once(self):
        cpu = monitor.get_cpu_usage(interval=None)
        mem = monitor.get_memory()
        disk = monitor.get_disk()
        net = self.net_tracker.sample()
        uptime = monitor.format_uptime(monitor.get_uptime_seconds())
        info = monitor.get_system_info()

        if cpu is not None:
            self.cpu_history.append(float(cpu))
            self.cpu_history = self.cpu_history[-config.CPU_HISTORY_LENGTH:]

        cores = monitor.get_cpu_count()
        core_text = f"{cores['logical'] or '?'} logical"
        if cores["physical"]:
            core_text += f" / {cores['physical']} physical"

        self.cpu_card.update(cpu, f"Cores: {core_text}")
        self.ram_card.update(
            mem["percent"],
            f"Used {monitor.format_bytes(mem['used'])} / "
            f"Total {monitor.format_bytes(mem['total'])}",
        )
        self.disk_card.update(
            disk["percent"],
            f"{disk['path']}  Free {monitor.format_bytes(disk['free'])} / "
            f"Total {monitor.format_bytes(disk['total'])}",
        )

        health = overall_health(cpu, mem["percent"], disk["percent"])
        self.overall_banner.config(
            text=f"Overall Status: {health}",
            fg=OVERALL_COLORS.get(health, TEXT),
        )

        self.net_rate_label.config(
            text=f"↑ Upload: {monitor.format_rate(net['upload_rate'])}   "
                 f"↓ Download: {monitor.format_rate(net['download_rate'])}"
        )
        self.net_total_label.config(
            text=f"Total sent {monitor.format_bytes(net['sent'])}   "
                 f"Total received {monitor.format_bytes(net['received'])}"
        )

        self.sys_label.config(
            text=f"Hostname: {info['hostname']}\n"
                 f"OS: {info['os']}\n"
                 f"Python: {info['python_version']}\n"
                 f"Uptime: {uptime}"
        )

        procs = monitor.get_top_processes()
        if procs:
            lines = ["Process                    CPU%   MEM%"]
            for p in procs:
                lines.append(f"{p['name']:<28} {p['cpu_percent']:>5.1f}  "
                             f"{p['memory_percent']:>5.1f}")
            self.proc_label.config(text="\n".join(lines))
        else:
            self.proc_label.config(text="Process info unavailable")

        self._draw_graph()
        self.updated_label.config(
            text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

    def _draw_graph(self):
        self.graph.delete("all")
        self.graph.update_idletasks()
        width = max(self.graph.winfo_width(), 200)
        height = 86
        self.graph.create_line(0, height - 1, width, height - 1, fill="#334155")
        if len(self.cpu_history) < 2:
            return
        step = width / max(len(self.cpu_history) - 1, 1)
        points = []
        for i, value in enumerate(self.cpu_history):
            y = height - 6 - (min(max(value, 0.0), 100.0) / 100.0) * (height - 14)
            points.extend([i * step, y])
        self.graph.create_line(*points, fill=ACCENT, width=2)


def main():
    root = tk.Tk()
    try:
        from ctypes import windll  # crisp text on Windows HiDPI
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    ServerPulseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
