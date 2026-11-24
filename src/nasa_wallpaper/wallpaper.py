"""Cross-platform wallpaper setter.

Supports:
  Windows  – ctypes (SystemParametersInfoW)
  Linux    – auto-detects desktop environment / window manager:
             GNOME, Cinnamon, MATE, KDE Plasma, XFCE, Hyprland (hyprpaper/swww/swaybg),
             Sway, i3, LXDE/LXQt, Deepin, Budgie, Pantheon
  macOS    – osascript
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, logging it, and suppressing errors by default."""
    log.debug("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def _has(binary: str) -> bool:
    return shutil.which(binary) is not None


def _detect_linux_desktop() -> str:
    """Return a lowercase token describing the current Linux desktop."""
    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP", "")
        or os.environ.get("DESKTOP_SESSION", "")
    ).lower()
    return desktop


# ---------------------------------------------------------------------------
# Per-desktop setters
# ---------------------------------------------------------------------------

def _set_gnome(path: str) -> bool:
    """GNOME / Unity / Budgie / Pantheon via gsettings."""
    if not _has("gsettings"):
        return False
    uri = Path(path).as_uri()
    _run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri])
    _run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri])
    _run(["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"])
    log.info("Wallpaper set via gsettings (GNOME)")
    return True


def _set_cinnamon(path: str) -> bool:
    if not _has("gsettings"):
        return False
    uri = Path(path).as_uri()
    _run(["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", uri])
    _run(["gsettings", "set", "org.cinnamon.desktop.background", "picture-options", "zoom"])
    log.info("Wallpaper set via gsettings (Cinnamon)")
    return True


def _set_mate(path: str) -> bool:
    if not _has("gsettings"):
        return False
    _run(["gsettings", "set", "org.mate.background", "picture-filename", path])
    log.info("Wallpaper set via gsettings (MATE)")
    return True


def _set_kde(path: str) -> bool:
    """KDE Plasma ≥5 via DBus script."""
    if not _has("qdbus") and not _has("qdbus6") and not _has("qdbus-qt5"):
        return False
    script = f"""
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {{
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file://{path}");
}}
"""
    _run([
        "qdbus", "org.kde.plasmashell", "/PlasmaShell",
        "org.kde.PlasmaShell.evaluateScript", script,
    ])
    log.info("Wallpaper set via qdbus (KDE Plasma)")
    return True


def _set_xfce(path: str) -> bool:
    if not _has("xfconf-query"):
        return False
    # Try to discover the active monitor property
    result = _run(["xfconf-query", "-c", "xfce4-desktop", "-l"])
    props = [
        line.strip()
        for line in (result.stdout or "").splitlines()
        if line.strip().endswith("/last-image")
    ]
    if not props:
        props = ["/backdrop/screen0/monitor0/workspace0/last-image"]
    for prop in props:
        _run(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", path])
    log.info("Wallpaper set via xfconf-query (XFCE)")
    return True


def _set_hyprland(path: str) -> bool:
    """Hyprland – try hyprpaper, then swww, then swaybg."""
    if _has("hyprctl"):
        # Try hyprpaper (if the user runs it)
        result = _run(["hyprctl", "hyprpaper", "listloaded"])
        if result.returncode == 0:
            _run(["hyprctl", "hyprpaper", "preload", path])
            _run(["hyprctl", "hyprpaper", "wallpaper", f",{path}"])
            log.info("Wallpaper set via hyprctl hyprpaper")
            return True

    if _has("swww"):
        _run(["swww", "img", path])
        log.info("Wallpaper set via swww")
        return True

    if _has("swaybg"):
        # swaybg is a persistent process – kill old one first
        _run(["pkill", "-x", "swaybg"])
        subprocess.Popen(
            ["swaybg", "-i", path, "-m", "fill"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        log.info("Wallpaper set via swaybg")
        return True

    return False


def _set_sway(path: str) -> bool:
    if not _has("swaymsg"):
        return False
    _run(["swaymsg", "output", "*", "bg", path, "fill"])
    log.info("Wallpaper set via swaymsg (Sway)")
    return True


def _set_feh(path: str) -> bool:
    """Fallback for X11 WMs (i3, bspwm, openbox, …)."""
    if not _has("feh"):
        return False
    _run(["feh", "--bg-fill", path])
    log.info("Wallpaper set via feh")
    return True


def _set_nitrogen(path: str) -> bool:
    if not _has("nitrogen"):
        return False
    _run(["nitrogen", "--set-auto", "--save", path])
    log.info("Wallpaper set via nitrogen")
    return True


def _set_deepin(path: str) -> bool:
    if not _has("gsettings"):
        return False
    _run([
        "gsettings", "set", "com.deepin.wrap.gnome.desktop.background",
        "picture-uri", Path(path).as_uri(),
    ])
    log.info("Wallpaper set via gsettings (Deepin)")
    return True


def _set_lxde(path: str) -> bool:
    if not _has("pcmanfm"):
        return False
    _run(["pcmanfm", "--set-wallpaper", path])
    log.info("Wallpaper set via pcmanfm (LXDE)")
    return True


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

_LINUX_DISPATCH: list[tuple[list[str], callable]] = [
    # Desktop keywords → setter function
    (["hyprland"], _set_hyprland),
    (["sway"], _set_sway),
    (["gnome", "unity", "budgie", "pantheon", "pop"], _set_gnome),
    (["cinnamon"], _set_cinnamon),
    (["mate"], _set_mate),
    (["kde", "plasma"], _set_kde),
    (["xfce"], _set_xfce),
    (["deepin"], _set_deepin),
    (["lxde"], _set_lxde),
]


def _set_linux(path: str) -> None:
    desktop = _detect_linux_desktop()
    log.debug("Detected Linux desktop: %r", desktop)

    # Try the matched desktop first
    for keywords, setter in _LINUX_DISPATCH:
        if any(kw in desktop for kw in keywords):
            if setter(path):
                return

    # If nothing matched or matched setter failed, try all setters
    for setter in [s for _, s in _LINUX_DISPATCH]:
        try:
            if setter(path):
                return
        except Exception:
            continue

    # Last-resort generic fallbacks
    for setter in [_set_feh, _set_nitrogen]:
        try:
            if setter(path):
                return
        except Exception:
            continue

    log.error("Could not set wallpaper – no supported desktop tool found")


def _set_windows(path: str) -> None:
    import ctypes
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    if result:
        log.info("Wallpaper set via SystemParametersInfoW (Windows)")
    else:
        log.error("SystemParametersInfoW failed")


def _set_macos(path: str) -> None:
    script = f'''
    tell application "System Events"
        tell every desktop
            set picture to POSIX file "{path}"
        end tell
    end tell
    '''
    _run(["osascript", "-e", script])
    log.info("Wallpaper set via osascript (macOS)")


def set_wallpaper(path: str) -> None:
    """Set the desktop wallpaper on the current platform.

    *path* must be an absolute path to an image file.
    """
    path = str(Path(path).resolve())
    if not Path(path).is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    system = platform.system().lower()
    if system == "windows":
        _set_windows(path)
    elif system == "darwin":
        _set_macos(path)
    elif system == "linux":
        _set_linux(path)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
