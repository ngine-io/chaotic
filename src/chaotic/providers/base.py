"""Provider base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from chaotic.excludes import excluded_reason
from chaotic.log import log


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
