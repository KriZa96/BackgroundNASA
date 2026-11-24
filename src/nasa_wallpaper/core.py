"""Core logic – orchestrates downloading + setting the wallpaper."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from . import apod, config, network, wallpaper

log = logging.getLogger(__name__)


def _already_ran_today() -> bool:
    """Return True if we already successfully ran today."""
    last_run_file = config.get_last_run_file()
    if last_run_file.exists():
        try:
            last_date_str = last_run_file.read_text().strip()
            return last_date_str == date.today().isoformat()
        except OSError:
            pass
    return False


def _mark_ran_today() -> None:
    """Record that we ran successfully today."""
    config.get_last_run_file().write_text(date.today().isoformat())


def _cleanup_old_images(data_dir: Path, keep_name: str) -> None:
    """Remove old downloaded images, keeping only *keep_name*."""
    for f in data_dir.glob("*.jpg"):
        if f.name != keep_name:
            log.debug("Removing old image: %s", f)
            f.unlink(missing_ok=True)
    for f in data_dir.glob("*.png"):
        if f.name != keep_name:
            f.unlink(missing_ok=True)


def run(force: bool = False) -> None:
    """Main entry point: download today's APOD image and set it as wallpaper.

    Args:
        force: Run even if we already ran today.
    """
    cfg = config.load_config()

    if not force and _already_ran_today():
        log.info("Already ran today (%s), skipping. Use --force to override.", date.today())
        return

    # Wait for internet (useful at boot)
    if not network.is_online():
        log.info("Waiting for internet connection…")
        if not network.wait_for_internet(max_wait=300):
            log.error("No internet connection. Aborting.")
            return

    # Fetch an image APOD
    api_key = cfg.get("api_key", "DEMO_KEY")
    max_retries = cfg.get("max_retries", 10)
    entry = apod.fetch_image_apod(api_key=api_key, max_retries=max_retries)

    # Choose the best URL (prefer HD)
    image_url = entry.get("hdurl") or entry["url"]
    image_date = entry.get("date", date.today().isoformat())
    title = entry.get("title", "Unknown")

    # Determine file extension from URL
    ext = ".jpg"
    url_lower = image_url.lower()
    for candidate in (".png", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"):
        if candidate in url_lower:
            ext = candidate
            break

    # Download
    data_dir = config.get_data_dir()
    filename = f"{image_date}{ext}"
    dest_path = data_dir / filename

    if not dest_path.exists():
        apod.download_image(image_url, str(dest_path))
    else:
        log.info("Image already downloaded: %s", dest_path)

    # Set wallpaper
    wallpaper.set_wallpaper(str(dest_path))

    # Cleanup old images (unless configured to keep them)
    if not cfg.get("keep_old_images", False):
        _cleanup_old_images(data_dir, filename)

    _mark_ran_today()
    log.info("✓ Wallpaper set to: %s (%s)", title, image_date)
