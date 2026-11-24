"""Platform-specific autostart installer.

Linux:   systemd user timer (runs daily + on boot after network-online)
Windows: Task Scheduler task (runs daily + on logon)
macOS:   launchd plist (runs daily + on load)
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def _find_executable() -> str:
    """Return the path to the nasa-wallpaper executable."""
    # If installed via pip, 'nasa-wallpaper' should be on PATH
    exe = shutil.which("nasa-wallpaper")
    if exe:
        return exe
    # Fallback: run the module
    return f"{sys.executable} -m nasa_wallpaper"


# ---------------------------------------------------------------------------
# Linux – systemd user service + timer
# ---------------------------------------------------------------------------

_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"

_SERVICE_UNIT = """\
[Unit]
Description=NASA Astronomy Picture of the Day wallpaper
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart={exe} run
Environment=DISPLAY={display}
Environment=WAYLAND_DISPLAY={wayland}
Environment=XDG_CURRENT_DESKTOP={desktop}
Environment=DBUS_SESSION_BUS_ADDRESS={dbus}

[Install]
WantedBy=default.target
"""

_TIMER_UNIT = """\
[Unit]
Description=Daily NASA wallpaper update

[Timer]
OnBootSec=30s
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""


def _install_linux() -> None:
    exe = _find_executable()
    _SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)

    service_path = _SYSTEMD_DIR / "nasa-wallpaper.service"
    timer_path = _SYSTEMD_DIR / "nasa-wallpaper.timer"

    service_content = _SERVICE_UNIT.format(
        exe=exe,
        display=os.environ.get("DISPLAY", ":0"),
        wayland=os.environ.get("WAYLAND_DISPLAY", ""),
        desktop=os.environ.get("XDG_CURRENT_DESKTOP", ""),
        dbus=os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
    )

    service_path.write_text(service_content)
    timer_path.write_text(_TIMER_UNIT)

    log.info("Created %s", service_path)
    log.info("Created %s", timer_path)

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "--now", "nasa-wallpaper.timer"], check=False)
    log.info("✓ systemd timer enabled. Wallpaper will update daily and 30s after boot.")
    print(f"✓ Installed systemd timer. Files:")
    print(f"  {service_path}")
    print(f"  {timer_path}")
    print()
    print("Check status:  systemctl --user status nasa-wallpaper.timer")
    print("Run now:        systemctl --user start nasa-wallpaper.service")
    print("View logs:      journalctl --user -u nasa-wallpaper.service")


def _uninstall_linux() -> None:
    subprocess.run(["systemctl", "--user", "disable", "--now", "nasa-wallpaper.timer"], check=False)
    subprocess.run(["systemctl", "--user", "disable", "nasa-wallpaper.service"], check=False)
    for name in ("nasa-wallpaper.service", "nasa-wallpaper.timer"):
        path = _SYSTEMD_DIR / name
        if path.exists():
            path.unlink()
            log.info("Removed %s", path)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    print("✓ Autostart removed.")


# ---------------------------------------------------------------------------
# Windows – Task Scheduler
# ---------------------------------------------------------------------------

def _install_windows() -> None:
    exe = _find_executable()
    task_name = "NASAWallpaper"

    # Create the task via schtasks
    # Runs daily at 8:00 AM and on logon
    cmds = [
        [
            "schtasks", "/Create", "/TN", task_name, "/TR", f'"{exe}" run',
            "/SC", "DAILY", "/ST", "08:00", "/F",
            "/RL", "LIMITED",
        ],
        [
            "schtasks", "/Create", "/TN", f"{task_name}OnLogon", "/TR", f'"{exe}" run',
            "/SC", "ONLOGON", "/F",
            "/RL", "LIMITED",
            "/DELAY", "0000:30",
        ],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log.info("Task created: %s", cmd[3])
        else:
            log.error("Failed to create task: %s", result.stderr)

    print(f"✓ Task Scheduler tasks created: {task_name}, {task_name}OnLogon")
    print("  Runs daily at 08:00 and 30 seconds after logon.")
    print(f"  Run now:  schtasks /Run /TN {task_name}")


def _uninstall_windows() -> None:
    for name in ("NASAWallpaper", "NASAWallpaperOnLogon"):
        subprocess.run(
            ["schtasks", "/Delete", "/TN", name, "/F"],
            capture_output=True, text=True,
        )
    print("✓ Task Scheduler tasks removed.")


# ---------------------------------------------------------------------------
# macOS – launchd
# ---------------------------------------------------------------------------

_PLIST_DIR = Path.home() / "Library" / "LaunchAgents"
_PLIST_NAME = "com.nasa-wallpaper.plist"

_PLIST_CONTENT = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nasa-wallpaper</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
        <string>run</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/nasa-wallpaper.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/nasa-wallpaper.err</string>
</dict>
</plist>
"""


def _install_macos() -> None:
    exe = _find_executable()
    _PLIST_DIR.mkdir(parents=True, exist_ok=True)
    plist_path = _PLIST_DIR / _PLIST_NAME
    plist_path.write_text(_PLIST_CONTENT.format(exe=exe))
    subprocess.run(["launchctl", "load", str(plist_path)], check=False)
    print(f"✓ launchd agent installed: {plist_path}")
    print("  Runs daily at 08:00 and on login.")


def _uninstall_macos() -> None:
    plist_path = _PLIST_DIR / _PLIST_NAME
    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
    if plist_path.exists():
        plist_path.unlink()
    print("✓ launchd agent removed.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def install() -> None:
    system = platform.system().lower()
    if system == "linux":
        _install_linux()
    elif system == "windows":
        _install_windows()
    elif system == "darwin":
        _install_macos()
    else:
        log.error("Unsupported platform: %s", system)


def uninstall() -> None:
    system = platform.system().lower()
    if system == "linux":
        _uninstall_linux()
    elif system == "windows":
        _uninstall_windows()
    elif system == "darwin":
        _uninstall_macos()
    else:
        log.error("Unsupported platform: %s", system)
