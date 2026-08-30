"""Apache CloudStack provider.

Requires ``CLOUDSTACK_API_ENDPOINT``, ``CLOUDSTACK_API_KEY`` and
``CLOUDSTACK_API_SECRET``.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import cached_property

from cs import CloudStack

from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target


class CloudStackChaotic(RestartChaotic):
    """Stop and start a random CloudStack instance."""

    @cached_property
    def client(self) -> CloudStack:
        """API client, created on first use so that importing stays side effect free."""
        return CloudStack(
            endpoint=os.getenv("CLOUDSTACK_API_ENDPOINT", ""),
            key=os.getenv("CLOUDSTACK_API_KEY", ""),
            secret=os.getenv("CLOUDSTACK_API_SECRET", ""),
        )

    def list_targets(self) -> Sequence[Target]:
        # A tag is mandatory here on purpose: without one, every instance in the
        # account would become a chaos candidate.
        tag = self.configs.get("tag")
        if not tag:
            log.warning("No 'tag' configured, refusing to consider all instances")
            return []

        log.info("Querying with tag: %s=%s", tag.get("key"), tag.get("value"))
        instances = (
            self.client.listVirtualMachines(
                tags=[tag],
                projectid=self.configs.get("projectid"),
                zoneid=self.configs.get("zoneid"),
                fetch_list=True,
            )
            or []
        )
        return [Target(id=instance["id"], name=instance["name"], raw=instance) for instance in instances]

    def stop(self, target: Target) -> None:
        self.client.stopVirtualMachine(id=target.id)

    def start(self, target: Target) -> None:
        self.client.startVirtualMachine(id=target.id)
