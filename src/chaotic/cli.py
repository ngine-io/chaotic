"""Command line entry point.

Settings can come from three places; the more explicit one wins::

    --config / --interval  >  $CHAOTIC_CONFIG / $CHAOTIC_INTERVAL  >  built-in default
"""

from __future__ import annotations

import os
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence

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
    """Build the argument parser.

    Both value options default to ``None`` so that "not passed" can be told
    apart from "passed the default", which is what makes the env var fallback
    work.
    """
    parser = ArgumentParser(prog="chaotic-ngine", description="Chaos for Clouds.")
    parser.add_argument("--periodic", help="run periodic", action="store_true")
    parser.add_argument(
        "--interval",
        help=f"set interval in minutes, or $CHAOTIC_INTERVAL, default {DEFAULT_INTERVAL_MINUTES}",
        type=int,
        default=None,
    )
    parser.add_argument("--version", help="show version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--config",
        help=f"use config file, or $CHAOTIC_CONFIG, default: {DEFAULT_CONFIG_SOURCE}",
        type=str,
        default=None,
    )
    return parser


def resolve_config_source(args: Namespace) -> str:
    """Return the config source, honouring CLI over env over default."""
    return args.config or os.environ.get("CHAOTIC_CONFIG") or DEFAULT_CONFIG_SOURCE


def resolve_interval(args: Namespace) -> int:
    """Return the interval in minutes, honouring CLI over env over default.

    Raises:
        ChaoticError: If the value is not a positive integer.
    """
    if args.interval is not None:
        interval = int(args.interval)
    else:
        raw = os.environ.get("CHAOTIC_INTERVAL")
        if raw is None:
            return DEFAULT_INTERVAL_MINUTES
        try:
            interval = int(raw)
        except ValueError as exc:
            raise ChaoticError(f"CHAOTIC_INTERVAL must be an integer, got {raw!r}") from exc

    if interval < 1:
        raise ChaoticError(f"Interval must be at least 1 minute, got {interval}")
    return interval


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
        config_source = resolve_config_source(args)
        if args.periodic:
            run_periodic(interval=resolve_interval(args), config_source=config_source)
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
