"""Logging setup.

Importing this module has no side effects; call :func:`configure_logging` once
during start up (the CLI does it for you). Library users keep full control over
their own logging configuration.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

DEFAULT_LOG_CONFIG = "logging.ini"
DEFAULT_LOG_LEVEL = "INFO"
FALLBACK_FORMAT = "%(asctime)s - %(name)s:%(levelname)s:%(message)s"

log: logging.Logger = logging.getLogger("chaotic")


def configure_logging(config_file: str | os.PathLike[str] | None = None, level: str | None = None) -> logging.Logger:
    """Configure the root logger and return chaotic's own logger.

    A ``logging.ini`` style file wins when it exists, which is how the container
    image gets JSON logs. Otherwise a plain stdout handler is installed.

    Args:
        config_file: Path to a :mod:`logging.config` file. Defaults to
            ``$CHAOTIC_LOG_CONFIG`` or ``logging.ini`` in the current directory.
        level: Log level for the fallback handler. Defaults to
            ``$CHAOTIC_LOG_LEVEL`` or ``INFO``.
    """
    path = Path(config_file or os.environ.get("CHAOTIC_LOG_CONFIG", DEFAULT_LOG_CONFIG))

    if path.is_file():
        fileConfig(path, disable_existing_loggers=False)
    else:
        # force=True keeps this authoritative: without it basicConfig silently
        # does nothing as soon as anything else has touched the root logger.
        logging.basicConfig(
            stream=sys.stdout,
            level=(level or os.environ.get("CHAOTIC_LOG_LEVEL", DEFAULT_LOG_LEVEL)).upper(),
            format=FALLBACK_FORMAT,
            force=True,
        )
    return log
