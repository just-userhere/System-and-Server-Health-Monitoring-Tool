"""ServerPulse configuration.

All tunable thresholds and refresh settings live here so the rest of
the codebase never scatters magic numbers around.
"""

# Health thresholds (percentages). Shared by CPU, RAM and Disk.
WARNING_THRESHOLD = 70.0
CRITICAL_THRESHOLD = 85.0

# GUI auto-refresh interval in milliseconds (2 seconds by default).
REFRESH_INTERVAL_MS = 2000

# How many recent CPU samples to keep for the mini history graph.
CPU_HISTORY_LENGTH = 60

# How many top processes to show in the optional process table.
TOP_PROCESS_COUNT = 5

# Disk path to monitor. None means "auto-detect":
#   Windows -> "C:\\", Linux/macOS -> "/"
DISK_PATH = None
