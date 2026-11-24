"""Command-line interface for nasa-wallpaper."""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nasa-wallpaper",
        description="Set your desktop wallpaper to NASA's Astronomy Picture of the Day.",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    sub = parser.add_subparsers(dest="command")

    # --- run ---
    run_parser = sub.add_parser("run", help="Download today's APOD and set it as wallpaper")
    run_parser.add_argument(
        "-f", "--force", action="store_true",
        help="Run even if already ran today",
    )
    run_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )

    # --- install ---
    install_parser = sub.add_parser(
        "install", help="Install autostart (systemd timer on Linux, Task Scheduler on Windows)"
    )
    install_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )

    # --- uninstall ---
    uninstall_parser = sub.add_parser(
        "uninstall", help="Remove autostart configuration"
    )
    uninstall_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )

    # --- config ---
    config_parser = sub.add_parser("config", help="Show or edit configuration")
    config_parser.add_argument(
        "--api-key", type=str, default=None,
        help="Set your NASA API key (get one free at https://api.nasa.gov)",
    )
    config_parser.add_argument(
        "--keep-old-images", type=str, choices=["true", "false"], default=None,
        help="Whether to keep old downloaded images",
    )
    config_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        # Default to "run" when invoked without arguments
        args.command = "run"
        args.force = False
        args.verbose = False

    _setup_logging(getattr(args, "verbose", False))

    if args.command == "run":
        from .core import run
        try:
            run(force=args.force)
        except Exception as exc:
            logging.error("Failed: %s", exc)
            return 1

    elif args.command == "install":
        from .installer import install
        install()

    elif args.command == "uninstall":
        from .installer import uninstall
        uninstall()

    elif args.command == "config":
        from .config import load_config, save_config
        cfg = load_config()
        changed = False
        if args.api_key is not None:
            cfg["api_key"] = args.api_key
            changed = True
        if args.keep_old_images is not None:
            cfg["keep_old_images"] = args.keep_old_images == "true"
            changed = True
        if changed:
            save_config(cfg)
            print("Configuration updated.")
        else:
            import json
            from .config import get_config_path
            print(f"Config file: {get_config_path()}")
            print(json.dumps(cfg, indent=2))

    return 0


def entry_point() -> None:
    sys.exit(main())


if __name__ == "__main__":
    entry_point()
