"""Network connectivity check – pure Python, no ping subprocess."""

from __future__ import annotations

import logging
import socket
import time

log = logging.getLogger(__name__)

CHECK_HOSTS = [
    ("api.nasa.gov", 443),
    ("1.1.1.1", 53),
    ("8.8.8.8", 53),
]


def is_online(timeout: float = 5.0) -> bool:
    """Return True if any of the probe hosts are reachable."""
    for host, port in CHECK_HOSTS:
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return True
        except OSError:
            continue
    return False


def wait_for_internet(max_wait: int = 300, interval: int = 5) -> bool:
    """Block until internet is available, up to *max_wait* seconds.

    Returns True if internet became available, False on timeout.
    """
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        if is_online():
            log.info("Internet connection established")
            return True
        log.debug("No internet yet, retrying in %ds…", interval)
        time.sleep(interval)
    log.error("Timed out waiting for internet after %ds", max_wait)
    return False
