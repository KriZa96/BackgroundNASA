"""Configuration and data directory management."""

from __future__ import annotations

import json
import logging
import os
import platform
from pathlib import Path

log = logging.getLogger(__name__)

APP_NAME = "nasa-wallpaper"

# Default config
DEFAULTS = {
    "api_key": "DEMO_KEY",
    "max_retries": 10,
    "keep_old_images": False,
}


def get_data_dir() -> Path:
    """Return the platform-appropriate data directory and ensure it exists."""
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    data_dir = base / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """Return the platform-appropriate config directory and ensure it exists."""
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> dict:
    """Load config from disk, falling back to defaults."""
    config = dict(DEFAULTS)
    path = get_config_path()
    if path.exists():
        try:
            with open(path) as fh:
                user_config = json.load(fh)
            config.update(user_config)
            log.debug("Config loaded from %s", path)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Could not read config %s: %s", path, exc)
    return config


def save_config(config: dict) -> None:
    """Write config to disk."""
    path = get_config_path()
    with open(path, "w") as fh:
        json.dump(config, fh, indent=2)
    log.info("Config saved to %s", path)


def get_last_run_file() -> Path:
    return get_data_dir() / "last_run.txt"
