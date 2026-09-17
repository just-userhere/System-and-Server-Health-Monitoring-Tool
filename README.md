# ServerPulse

**System & Server Health Monitoring Tool** — a clean, beginner-friendly Python desktop app that monitors the computer it runs on: CPU, RAM, disk, network, uptime, system info, and top processes, with simple rule-based health alerts.

> Read-only monitoring only. ServerPulse never kills processes, shuts down the system, restarts services, or modifies the OS.

## Overview

ServerPulse collects live system metrics with `psutil`, classifies each metric against configurable thresholds, computes an overall HEALTHY / WARNING / CRITICAL status, and displays everything in a Tkinter dashboard that auto-refreshes every 2 seconds.

## Features

- **CPU monitoring** — usage %, core counts, live history sparkline
- **RAM monitoring** — usage %, used / total with progress card
- **Disk monitoring** — usage %, free / total (auto-detects `C:\` on Windows, `/` elsewhere)
- **Network monitoring** — upload / download rates + total sent / received
- **System uptime** — human-readable (`2 Days 04 Hours 18 Minutes`)
- **System information** — hostname, OS, platform, Python version
- **Overall health status** — HEALTHY / WARNING / CRITICAL from worst-metric rule
- **Visual alerts** — each card turns green / amber / red at its threshold
- **Top 5 processes** — process name, CPU %, memory % (best-effort, never crashes)
- **Auto-refresh** — non-blocking `after()` loop, plus manual Refresh button

## Tech Stack

- Python 3 (standard library + Tkinter for the GUI)
- [psutil](https://pypi.org/project/psutil/) for system metrics
- `unittest` for tests (standard library, no extra dependency)

## Architecture

```text
ServerPulse/
├── main.py                  # Tkinter dashboard + startup (after() refresh loop)
├── monitor.py               # metric collection via psutil (graceful fallbacks)
├── alerts.py                # threshold classification + overall health rule
├── config.py                # WARNING/CRITICAL thresholds, refresh interval
├── requirements.txt
├── tests/test_monitor.py    # unit + live-metric tests
├── assets/                  # screenshots (added later, none fabricated)
├── maintenance/status.json  # automated-maintenance metadata (see below)
└── .github/workflows/maintenance.yml
```

## How It Works

1. `psutil` collects system metrics (CPU %, memory, disk, network counters, boot time).
2. `monitor.py` normalises them and returns `None`/`N/A`-safe values on any failure.
3. `alerts.py` classifies each percentage: < 70% NORMAL, 70–84% WARNING, 85%+ CRITICAL.
4. Overall health = worst of CPU / RAM / disk (any critical → CRITICAL, else any warning → WARNING, else HEALTHY).
5. `main.py` renders the Tkinter dashboard and re-runs the update via `after()` every 2 seconds without blocking the UI.

## Installation

```bash
git clone https://github.com/just-userhere/System-and-Server-Health-Monitoring-Tool.git
cd System-and-Server-Health-Monitoring-Tool
# or: cd ServerPulse   (if using the standalone project folder)

py -m venv venv
```

Activate the environment:

Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
source venv/bin/activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
py main.py
# Linux/macOS: python3 main.py
```

Run from inside the `ServerPulse/` directory.

## Testing

```bash
py -m unittest discover -s tests -v
```

Tests cover: threshold classification, overall-health logic, uptime/byte formatting, and live CPU / memory / disk / system-info collection.

## Screenshots

Screenshots will be added under `assets/` once captured from a real run:

- `assets/dashboard.png` — main dashboard
- `assets/dashboard-warning.png` — warning/critical state

## Automated Repository Maintenance

ServerPulse contains a GitHub Actions workflow at `.github/workflows/maintenance.yml` that runs approximately every 48 hours (plus manual `workflow_dispatch`). It updates `maintenance/status.json` with the latest maintenance timestamp and pushes a small `chore: update automated maintenance status` commit to the `master` branch — only when the file actually changed. This is automated repository maintenance, not a new application feature.

## Future Improvements

- Remote server monitoring
- Historical metrics / CSV report export
- Notification integrations (email/desktop)
- User-configurable thresholds in the UI
- Service monitoring

## Disclaimer

Local monitoring tool only. It collects and displays information and does not modify system settings, terminate processes, or perform privileged operations.

## License

MIT — see [LICENSE](LICENSE).
