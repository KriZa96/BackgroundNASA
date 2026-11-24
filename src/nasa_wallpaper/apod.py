"""NASA APOD API client – fetches the Astronomy Picture of the Day."""

from __future__ import annotations

import logging
import random
from datetime import date, timedelta
from typing import Optional

import requests

log = logging.getLogger(__name__)

APOD_URL = "https://api.nasa.gov/planetary/apod"
APOD_START_DATE = date(1995, 6, 16)  # first ever APOD

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def _is_image(entry: dict) -> bool:
    """Return True when the APOD entry is a downloadable image (not a video/gif/embed)."""
    if entry.get("media_type") != "image":
        return False
    url = entry.get("hdurl") or entry.get("url", "")
    # Reject animated GIFs
    if url.lower().endswith(".gif"):
        return False
    return True


def _random_date() -> date:
    """Return a random date between APOD_START_DATE and yesterday."""
    days_range = (date.today() - APOD_START_DATE).days
    return APOD_START_DATE + timedelta(days=random.randint(0, max(0, days_range - 1)))


def fetch_apod(
    api_key: str = "DEMO_KEY",
    target_date: Optional[date] = None,
    timeout: int = 30,
) -> dict:
    """Fetch a single APOD entry.  Raises on HTTP errors."""
    if target_date is None:
        target_date = date.today()
    params = {"api_key": api_key, "date": target_date.isoformat()}
    resp = requests.get(APOD_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_image_apod(
    api_key: str = "DEMO_KEY",
    max_retries: int = 10,
    timeout: int = 30,
) -> dict:
    """Return an APOD entry that is a real image.

    First tries today's picture, then falls back to random past dates.
    """
    # Try today first
    try:
        entry = fetch_apod(api_key=api_key, timeout=timeout)
        if _is_image(entry):
            log.info("Today's APOD is an image: %s", entry.get("title"))
            return entry
        log.info("Today's APOD is not an image (%s), picking a random one…", entry.get("media_type"))
    except requests.RequestException as exc:
        log.warning("Could not fetch today's APOD: %s", exc)

    # Fall back to random dates
    for attempt in range(1, max_retries + 1):
        rand_date = _random_date()
        try:
            entry = fetch_apod(api_key=api_key, target_date=rand_date, timeout=timeout)
            if _is_image(entry):
                log.info("Random APOD image found (%s): %s", rand_date, entry.get("title"))
                return entry
            log.debug("Attempt %d: %s is not an image, retrying…", attempt, rand_date)
        except requests.RequestException as exc:
            log.debug("Attempt %d failed: %s", attempt, exc)

    raise RuntimeError(f"Could not find an image APOD after {max_retries} retries")


def download_image(url: str, dest_path: str, timeout: int = 60) -> None:
    """Download an image from *url* and save it to *dest_path*."""
    log.info("Downloading %s → %s", url, dest_path)
    resp = requests.get(url, timeout=timeout, stream=True)
    resp.raise_for_status()
    with open(dest_path, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=1024 * 64):
            fh.write(chunk)
