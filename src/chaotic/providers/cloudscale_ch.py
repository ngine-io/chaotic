"""cloudscale.ch provider.

Requires ``CLOUDSCALE_API_TOKEN``.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import cached_property

from cloudscale import Cloudscale

from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target


class CloudscaleChChaotic(RestartChaotic):
    """Stop and start a random cloudscale.ch server."""

    @cached_property
    def client(self) -> Cloudscale:
        """API client, created on first use so that importing stays side effect free."""
        return Cloudscale(api_token=os.getenv("CLOUDSCALE_API_TOKEN", ""))

    def list_targets(self) -> Sequence[Target]:
        filter_tag = self.configs.get("filter_tag")
        log.info("Querying with filter_tag: %s", filter_tag)
        servers = self.client.server.get_all(filter_tag=filter_tag) or []
        return [Target(id=server["uuid"], name=server["name"], raw=server) for server in servers]

    def stop(self, target: Target) -> None:
        self.client.server.stop(uuid=target.id)

    def start(self, target: Target) -> None:
        self.client.server.start(uuid=target.id)
