"""Running a chaos plan, once or on a schedule."""

from __future__ import annotations

import sys
import time

import schedule

from chaotic.config import load_config
from chaotic.factory import ChaoticFactory
from chaotic.log import log

TICK_SECONDS = 1


def run_once(config_source: str) -> None:
    """Load the plan and run a single experiment.

    The config is read on every call on purpose: in periodic mode that means
    edits take effect without restarting the service.
    """
    config = load_config(config_source)

    chaos = ChaoticFactory().get_instance(config.kind)
    chaos.configure(configs=config.configs, dry_run=config.dry_run, excludes=config.excludes)
    chaos.action()


def run_periodic(interval: int = 1, config_source: str = "config.yaml") -> None:
    """Run an experiment now and then every ``interval`` minutes, forever."""
    log.info("Running periodic in intervals of %s minute(s)", interval)
    schedule.every(interval).minutes.do(run_once, config_source=config_source)
    schedule.run_all()

    while True:
        schedule.run_pending()
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(TICK_SECONDS)
