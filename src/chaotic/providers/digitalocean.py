"""DigitalOcean provider.

Requires ``DIGITALOCEAN_ACCESS_TOKEN``, which the vendor SDK reads itself.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import cached_property

import digitalocean

from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target


class DigitaloceanChaotic(RestartChaotic):
    """Shut down and power on a random droplet."""

    target_noun = "droplet"

    @cached_property
    def client(self) -> digitalocean.Manager:
        """API client, created on first use so that importing stays side effect free."""
        return digitalocean.Manager()

    def list_targets(self) -> Sequence[Target]:
        tag = self.configs.get("tag")
        log.info("Querying with tag: %s", tag)
        droplets = self.client.get_all_droplets(tag_name=tag) or []
        return [Target(id=str(droplet.id), name=droplet.name, raw=droplet) for droplet in droplets]

    def stop(self, target: Target) -> None:
        target.raw.shutdown()

    def start(self, target: Target) -> None:
        target.raw.power_on()
