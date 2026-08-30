"""Command line entry point."""

from __future__ import annotations

import os
from argparse import ArgumentParser
from typing import Sequence

import truststore

from chaotic.config import DEFAULT_CONFIG_SOURCE, load_env
from chaotic.errors import ChaoticError
from chaotic.log import configure_logging, log
from chaotic.runner import run_once, run_periodic
from chaotic.version import __version__

DEFAULT_INTERVAL_MINUTES = 1

EXIT_OK = 0
EXIT_FAILURE = 1


def build_parser() -> ArgumentParser:
    """Build the argument parser."""
    parser = ArgumentParser(prog="chaotic-ngine", description="Chaos for Clouds.")
    parser.add_argument("--periodic", help="run periodic", action="store_true")
    parser.add_argument(
        "--interval",
        help=f"set interval in minutes, default {DEFAULT_INTERVAL_MINUTES}",
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
    )
    parser.add_argument("--version", help="show version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--config",
        help=f"use config file, default: {DEFAULT_CONFIG_SOURCE}",
        type=str,
        default=DEFAULT_CONFIG_SOURCE,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run chaotic and return a process exit code."""
    args = build_parser().parse_args(argv)

    load_env()
    configure_logging()
    # Use the operating system trust store, so corporate CAs and self signed
    # Proxmox certificates work without extra configuration.
    truststore.inject_into_ssl()

    log.info("Starting version %s", __version__)

    try:
        config_source = os.environ.get("CHAOTIC_CONFIG", args.config)
        if args.periodic:
            run_periodic(interval=args.interval, config_source=config_source)
        else:
            run_once(config_source)
    except KeyboardInterrupt:
        log.info("Stopping...")
        log.info("done")
    except ChaoticError as exc:
        log.error("%s", exc)
        return EXIT_FAILURE
    except Exception:
        log.exception("Chaos run failed")
        return EXIT_FAILURE

    return EXIT_OK
