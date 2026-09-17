"""Threshold and overall-health logic for ServerPulse.

This is a simple rule-based system (not AI/prediction):

* Each metric percentage is classified as NORMAL / WARNING / CRITICAL.
* Overall health is the worst of the CPU, RAM and disk states:
  any CRITICAL -> CRITICAL, else any WARNING -> WARNING, else HEALTHY.
"""

from config import CRITICAL_THRESHOLD, WARNING_THRESHOLD

STATUS_NORMAL = "NORMAL"
STATUS_WARNING = "WARNING"
STATUS_CRITICAL = "CRITICAL"

HEALTHY = "HEALTHY"
HEALTH_WARNING = "WARNING"
HEALTH_CRITICAL = "CRITICAL"

# UI colours keyed by status (used by main.py).
STATUS_COLORS = {
    STATUS_NORMAL: "#22c55e",    # green
    STATUS_WARNING: "#f59e0b",   # amber
    STATUS_CRITICAL: "#ef4444",  # red
    "UNKNOWN": "#94a3b8",        # grey for N/A
}

OVERALL_COLORS = {
    HEALTHY: "#22c55e",
    HEALTH_WARNING: "#f59e0b",
    HEALTH_CRITICAL: "#ef4444",
}


def classify_metric(value):
    """Classify a 0-100 percentage into NORMAL / WARNING / CRITICAL.

    Returns "UNKNOWN" when value is None (metric unavailable).
    """
    if value is None:
        return "UNKNOWN"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if value >= CRITICAL_THRESHOLD:
        return STATUS_CRITICAL
    if value >= WARNING_THRESHOLD:
        return STATUS_WARNING
    return STATUS_NORMAL


def overall_health(cpu_percent=None, ram_percent=None, disk_percent=None):
    """Compute overall health from the three main metrics.

    Any unavailable (None) metric is ignored. If all are unavailable,
    the result is HEALTHY with nothing to warn about — the dashboard
    still shows N/A for the missing cards.
    """
    states = [
        classify_metric(cpu_percent),
        classify_metric(ram_percent),
        classify_metric(disk_percent),
    ]
    # Drop unknowns for the aggregate decision.
    known = [s for s in states if s != "UNKNOWN"]
    if not known:
        return HEALTHY
    if STATUS_CRITICAL in known:
        return HEALTH_CRITICAL
    if STATUS_WARNING in known:
        return HEALTH_WARNING
    return HEALTHY
