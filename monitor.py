"""System metric collection for ServerPulse (read-only, via psutil).

Every function degrades gracefully: on any psutil / permission /
platform problem it returns None (or "N/A"-friendly structures)
instead of raising, so one missing sensor never crashes the dashboard.
"""

import os
import platform
import socket
import sys
import time

import psutil

import config


def get_disk_path():
    """Return the disk path to monitor, honouring config.DISK_PATH."""
    if config.DISK_PATH:
        return config.DISK_PATH
    if os.name == "nt":
        return "C:\\"
    return "/"


def get_cpu_usage(interval=0.1):
    """Return current CPU usage percent, or None if unavailable."""
    try:
        value = psutil.cpu_percent(interval=interval)
        return float(value)
    except Exception:
        return None


def get_cpu_count():
    """Return {'logical': int|None, 'physical': int|None}."""
    try:
        logical = psutil.cpu_count(logical=True)
    except Exception:
        logical = None
    try:
        physical = psutil.cpu_count(logical=False)
    except Exception:
        physical = None
    return {"logical": logical, "physical": physical}


def get_memory():
    """Return dict with percent/used/available/total (bytes), Nones on failure."""
    try:
        mem = psutil.virtual_memory()
        return {
            "percent": float(mem.percent),
            "used": int(mem.used),
            "available": int(mem.available),
            "total": int(mem.total),
        }
    except Exception:
        return {"percent": None, "used": None, "available": None, "total": None}


def get_disk(path=None):
    """Return dict with percent/used/free/total for the given path."""
    target = path or get_disk_path()
    try:
        usage = psutil.disk_usage(target)
        return {
            "path": target,
            "percent": float(usage.percent),
            "used": int(usage.used),
            "free": int(usage.free),
            "total": int(usage.total),
        }
    except Exception:
        # Fall back: try the other common root once before giving up.
        try:
            fallback = "/" if target != "/" else os.path.expanduser("~")
            usage = psutil.disk_usage(fallback)
            return {
                "path": fallback,
                "percent": float(usage.percent),
                "used": int(usage.used),
                "free": int(usage.free),
                "total": int(usage.total),
            }
        except Exception:
            return {
                "path": target,
                "percent": None,
                "used": None,
                "free": None,
                "total": None,
            }


def get_network_totals():
    """Return {'sent': bytes, 'received': bytes} or Nones on failure."""
    try:
        counters = psutil.net_io_counters()
        if counters is None:
            return {"sent": None, "received": None}
        return {"sent": int(counters.bytes_sent), "received": int(counters.bytes_recv)}
    except Exception:
        return {"sent": None, "received": None}


class NetworkTracker:
    """Track upload/download rates between refreshes."""

    def __init__(self):
        self.prev = get_network_totals()
        self.prev_time = time.monotonic()

    def sample(self):
        """Return dict with totals plus per-second upload/download rates."""
        now = time.monotonic()
        current = get_network_totals()
        elapsed = max(now - self.prev_time, 1e-6)

        upload_rate = None
        download_rate = None
        try:
            if (
                self.prev.get("sent") is not None
                and current.get("sent") is not None
                and current["sent"] >= self.prev["sent"]
            ):
                upload_rate = (current["sent"] - self.prev["sent"]) / elapsed
            if (
                self.prev.get("received") is not None
                and current.get("received") is not None
                and current["received"] >= self.prev["received"]
            ):
                download_rate = (current["received"] - self.prev["received"]) / elapsed
        except Exception:
            upload_rate = None
            download_rate = None

        self.prev = current
        self.prev_time = now
        return {
            "sent": current["sent"],
            "received": current["received"],
            "upload_rate": upload_rate,
            "download_rate": download_rate,
        }


def get_uptime_seconds():
    """Return seconds since boot, or None if unavailable."""
    try:
        boot = psutil.boot_time()
        return max(time.time() - boot, 0.0)
    except Exception:
        return None


def format_uptime(total_seconds):
    """Format seconds as 'X Days Y Hours Z Minutes' (human readable)."""
    if total_seconds is None:
        return "N/A"
    try:
        total_seconds = int(total_seconds)
    except (TypeError, ValueError):
        return "N/A"
    if total_seconds < 0:
        total_seconds = 0
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days} Days {hours:02d} Hours {minutes:02d} Minutes"
    if hours > 0:
        return f"{hours} Hours {minutes:02d} Minutes"
    return f"{minutes} Minutes"


def format_bytes(num_bytes):
    """Format a byte count as '1.23 GB' etc. Returns 'N/A' for None."""
    if num_bytes is None:
        return "N/A"
    try:
        value = float(num_bytes)
    except (TypeError, ValueError):
        return "N/A"
    if value < 0:
        value = 0.0
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024.0 or unit == "PB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def format_rate(bytes_per_sec):
    """Format a per-second rate as '12.34 KB/s'. Returns 'N/A' for None."""
    if bytes_per_sec is None:
        return "N/A"
    try:
        value = float(bytes_per_sec)
    except (TypeError, ValueError):
        return "N/A"
    text = format_bytes(value)
    return f"{text}/s"


def get_system_info():
    """Return basic host info; every field falls back to 'N/A'/'Unknown'."""
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "Unknown"
    try:
        os_name = f"{platform.system()} {platform.release()}".strip() or "Unknown"
    except Exception:
        os_name = "Unknown"
    try:
        platform_detail = platform.platform() or "Unknown"
    except Exception:
        platform_detail = "Unknown"
    cores = get_cpu_count()
    return {
        "hostname": hostname or "Unknown",
        "os": os_name,
        "platform": platform_detail,
        "python_version": sys.version.split()[0],
        "cpu_logical": cores["logical"],
        "cpu_physical": cores["physical"],
    }


def get_top_processes(count=None):
    """Return up to `count` processes sorted by CPU%, best-effort only."""
    limit = count or config.TOP_PROCESS_COUNT
    try:
        # Non-blocking first pass initialises per-process CPU percentages.
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc.cpu_percent(interval=None)
            except Exception:
                continue
        time.sleep(0.1)
        rows = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                rows.append(
                    {
                        "pid": info.get("pid"),
                        "name": (info.get("name") or "unknown")[:28],
                        "cpu_percent": float(info.get("cpu_percent") or 0.0),
                        "memory_percent": float(info.get("memory_percent") or 0.0),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        rows.sort(key=lambda r: r["cpu_percent"], reverse=True)
        return rows[:limit]
    except Exception:
        return []
