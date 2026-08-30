"""Provider base classes.

Every provider is a :class:`Chaotic` subclass that knows how to run one chaos
experiment against one API. Most of them share the exact same experiment —
*pick a random machine, stop it, wait, start it again* — which lives in
:class:`RestartChaotic`. A provider only has to answer three questions:

* which machines are eligible (:meth:`RestartChaotic.list_targets`)
* how do I stop one (:meth:`RestartChaotic.stop`)
* how do I start one again (:meth:`RestartChaotic.start`)

Providers with a genuinely different experiment (Nomad drains nodes and signals
allocations) subclass :class:`Chaotic` and implement :meth:`Chaotic.action`.
"""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from chaotic.excludes import excluded_reason
from chaotic.log import log

DEFAULT_WAIT_BEFORE_RESTART_SECONDS = 60


@dataclass(frozen=True, slots=True)
class Target:
    """A single machine a provider may act on.

    Attributes:
        id: Provider specific identifier used for API calls.
        name: Human readable name, only ever used for logging.
        raw: The untouched API payload, for providers that need more than id and
            name (Proxmox needs the cluster node and the VM type, for example).
    """

    id: str
    name: str
    raw: Any = field(default=None, repr=False)


class Chaotic(ABC):
    """Base class for all chaos providers."""

    def __init__(self) -> None:
        self.configs: Mapping[str, Any] = {}
        self.dry_run: bool = False
        self.excludes: Mapping[str, Any] = {}

    def configure(
        self,
        configs: Mapping[str, Any] | None = None,
        dry_run: bool = False,
        excludes: Mapping[str, Any] | None = None,
    ) -> None:
        """Apply a chaos plan to this provider.

        Must be called before :meth:`action`. An active exclude window forces
        ``dry_run`` on, it never cancels the run outright — that way the logs
        still show which target *would* have been hit.
        """
        self.configs = configs or {}
        self.dry_run = dry_run
        self.excludes = excludes or {}

        reason = excluded_reason(self.excludes)
        if reason:
            log.info("%s, forcing dry-run", reason)
            self.dry_run = True

        if self.dry_run:
            log.info("Running in dry-run")

    @abstractmethod
    def action(self) -> None:
        """Run the chaos experiment once."""


class RestartChaotic(Chaotic):
    """Stop a randomly chosen target, wait, then start it again.

    Subclasses implement the three abstract hooks below and may override
    :meth:`skip_reason` to veto a target after it was chosen.
    """

    target_noun: str = "server"
    """Word used in log messages, e.g. ``server``, ``droplet`` or ``VM``."""

    @abstractmethod
    def list_targets(self) -> Sequence[Target]:
        """Return every target eligible for chaos, after applying config filters."""

    @abstractmethod
    def stop(self, target: Target) -> None:
        """Shut the target down."""

    @abstractmethod
    def start(self, target: Target) -> None:
        """Power the target back on."""

    def skip_reason(self, target: Target) -> str | None:  # noqa: ARG002  (overrides use it)
        """Return why the chosen target must be spared, or ``None`` to proceed."""
        return None

    @property
    def wait_before_restart(self) -> int:
        """Seconds to keep the target down before starting it again."""
        return int(self.configs.get("wait_before_restart", DEFAULT_WAIT_BEFORE_RESTART_SECONDS))

    def action(self) -> None:
        targets = self.list_targets()
        if not targets:
            log.info("No %ss found", self.target_noun)
            log.info("done")
            return

        target = random.choice(list(targets))
        log.info("Selected %s %s", self.target_noun, target.name)

        reason = self.skip_reason(target)
        if reason:
            log.info("Skipping %s %s: %s", self.target_noun, target.name, reason)
            log.info("done")
            return

        if self.dry_run:
            log.info("Dry-run, not restarting %s %s", self.target_noun, target.name)
            log.info("done")
            return

        log.info("Stopping %s %s", self.target_noun, target.name)
        self.stop(target)

        log.info("Sleeping for %s seconds", self.wait_before_restart)
        time.sleep(self.wait_before_restart)

        log.info("Starting %s %s", self.target_noun, target.name)
        self.start(target)

        log.info("done")
