# 🚀 NASA Wallpaper

**Set your desktop wallpaper to NASA's [Astronomy Picture of the Day](https://apod.nasa.gov/)** — automatically, every day.

Works on **Windows**, **macOS**, and **Linux** (GNOME, KDE, XFCE, Hyprland, Sway, Cinnamon, MATE, i3, and more).

![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-GPL--2.0-blue)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)

## How It Works

1. Fetches today's Astronomy Picture of the Day from NASA's API
2. If the APOD is a video, GIF, or other non-image format → picks a random past image instead
3. Downloads the HD image and sets it as your desktop wallpaper
4. Runs once per day — won't re-download if already ran today

## Installation

### Quick Install (recommended)

```bash
pip install .
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/KriZa96/BackgroundNASA.git
```

### That's it! Now run it:

```bash
nasa-wallpaper run
```

## Setup Autostart

The installer automatically sets up daily execution + startup trigger for your platform:

```bash
nasa-wallpaper install
```

| Platform | Method | What it does |
|----------|--------|--------------|
| **Linux** | systemd user timer | Runs daily at 08:00 + 30s after boot |
| **Windows** | Task Scheduler | Runs daily at 08:00 + 30s after logon |
| **macOS** | launchd agent | Runs daily at 08:00 + on login |

To remove autostart:

```bash
nasa-wallpaper uninstall
```

## Configuration

### Set a NASA API key (optional, but recommended)

The default `DEMO_KEY` works but is rate-limited. Get a **free** key at [api.nasa.gov](https://api.nasa.gov/):

```bash
nasa-wallpaper config --api-key YOUR_KEY_HERE
```

### View current config

```bash
nasa-wallpaper config
```

### Keep old images

By default, only the latest image is kept. To keep all past downloads:

```bash
nasa-wallpaper config --keep-old-images true
```

## Usage

```
nasa-wallpaper              # Download & set wallpaper (default action)
nasa-wallpaper run           # Same as above
nasa-wallpaper run --force   # Run even if already ran today
nasa-wallpaper install       # Set up autostart for your platform
nasa-wallpaper uninstall     # Remove autostart
nasa-wallpaper config        # View configuration
nasa-wallpaper --version     # Show version
```

## Supported Linux Desktops

| Desktop | Tool used |
|---------|-----------|
| GNOME / Ubuntu / Pop!_OS | `gsettings` |
| KDE Plasma | `qdbus` |
| XFCE | `xfconf-query` |
| Hyprland | `hyprpaper` / `swww` / `swaybg` |
| Sway | `swaymsg` |
| Cinnamon | `gsettings` |
| MATE | `gsettings` |
| Deepin | `gsettings` |
| LXDE | `pcmanfm` |
| i3 / bspwm / openbox | `feh` / `nitrogen` |
| Budgie / Pantheon | `gsettings` |

## File Locations

| | Linux | Windows | macOS |
|-|-------|---------|-------|
| **Config** | `~/.config/nasa-wallpaper/` | `%LOCALAPPDATA%\nasa-wallpaper\` | `~/Library/Application Support/nasa-wallpaper/` |
| **Images** | `~/.local/share/nasa-wallpaper/` | `%LOCALAPPDATA%\nasa-wallpaper\` | `~/Library/Application Support/nasa-wallpaper/` |

## Troubleshooting

### Linux: Check if the timer is running
```bash
systemctl --user status nasa-wallpaper.timer
journalctl --user -u nasa-wallpaper.service
```

### Force a re-run
```bash
nasa-wallpaper run --force
```

### Run with debug output
```bash
nasa-wallpaper run --verbose
```

## License

This program is free software; you can redistribute it and/or modify it under the terms of the **GNU General Public License v2** as published by the Free Software Foundation.

See [LICENSE](LICENSE) for the full text. Same license as the Linux kernel — copyleft, ensuring this software and all derivatives remain free and open source forever.
